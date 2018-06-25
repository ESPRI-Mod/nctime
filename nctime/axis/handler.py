#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: File handler for time axis.

"""

import logging
import os
import re
from copy import deepcopy as copy
from uuid import uuid4

import nco
import numpy as np
from fuzzywuzzy import fuzz, process

from constants import *
from custom_exceptions import *
from nctime.utils.constants import CLIM_SUFFIX, END_TIME_CORRECTION
from nctime.utils.custom_exceptions import *
from nctime.utils.misc import ncopen
from nctime.utils.time import time_inc, convert_time_units
from nctime.utils.time import truncated_timestamp, get_start_end_dates_from_filename, dates2str, num2date, date2num, \
    control_time_units, trunc


class File(object):
    """
    Handler providing methods to deal with file processing.

    :returns: The axis status
    :rtype: *File*

    """

    def __init__(self, ffp, pattern, ref_units, ref_calendar, correction):
        # Retrieve the file full path
        self.ffp = ffp
        # Retrieve the reference time units to use
        self.ref_units = ref_units
        # Retrieve the reference calendar to use
        self.ref_calendar = ref_calendar
        # If true dates from filename
        self.correction = correction
        # Retrieve the file size
        self.size = os.stat(self.ffp).st_size
        # Retrieve directory and filename full path
        self.directory, self.filename = os.path.split(ffp)
        # Remove "-clim.nc" suffix from filename if exists
        self.name = self.filename.replace(CLIM_SUFFIX, '.nc') if self.filename.endswith(CLIM_SUFFIX) else self.filename
        # Set variables for time axis diagnostic
        self.time_axis_rebuilt = None
        self.date_axis_rebuilt = None
        self.time_bounds_rebuilt = None
        self.date_bounds_rebuilt = None
        self.status = list()
        # Get netCDF time properties
        with ncopen(self.ffp) as nc:
            # Get frequency from file
            if 'frequency' in nc.ncattrs():
                self.frequency = nc.getncattr('frequency')
            else:
                key, score = process.extractOne('frequency', nc.ncattrs(), scorer=fuzz.partial_ratio)
                if score >= 80:
                    self.frequency = nc.getncattr(key)
                    logging.warning('Consider "{}" attribute instead of "frequency"'.format(key))
                else:
                    raise NoNetCDFAttribute('frequency', self.ffp)
            # Get time length and vector
            if 'time' not in nc.variables.keys():
                raise NoNetCDFVariable('time', self.ffp)
            self.length = nc.variables['time'].shape[0]
            if self.length == 0:
                raise EmptyTimeAxis(self.ffp)
            t = nc.variables['time'][:]
            self.time_axis = trunc(t, NDECIMALS)
            self.date_axis = dates2str(num2date(t, units=self.ref_units, calendar=self.ref_calendar))
            del t
            # Get time boundaries
            self.has_bounds = False
            if 'bounds' in nc.variables['time'].ncattrs():
                self.has_bounds = True
                self.tbnds = nc.variables['time'].bounds
                bnds = nc.variables[self.tbnds][:, :]
                self.time_bounds = trunc(bnds, NDECIMALS)
                self.date_bounds = np.column_stack((
                    dates2str(num2date(bnds[:, 0], units=self.ref_units, calendar=self.ref_calendar)),
                    dates2str(num2date(bnds[:, 1], units=self.ref_units, calendar=self.ref_calendar))
                ))
                del bnds
            # Get time units from file
            if 'units' not in nc.variables['time'].ncattrs():
                raise NoNetCDFAttribute('units', self.ffp, 'time')
            self.tunits = control_time_units(nc.variables['time'].units)
            # Get calendar from file
            if 'calendar' not in nc.variables['time'].ncattrs():
                raise NoNetCDFAttribute('calendar', self.ffp, 'time')
            self.calendar = nc.variables['time'].calendar
            # Get boolean on instantaneous time axis
            variable = unicode(self.filename.split('_')[0])
            if 'cell_methods' not in nc.variables[variable].ncattrs():
                raise NoNetCDFAttribute('cell_methods', self.ffp, variable)
            self.is_instant = False
            if 'time: point' in nc.variables[variable].cell_methods.lower():
                self.is_instant = True
        # Get time step increment from frequency property
        self.step, self.step_units = time_inc(self.frequency)
        # Convert reference time units into frequency units depending on the file (i.e., months/year/hours since ...)
        self.funits = convert_time_units(self.ref_units, self.frequency)
        # Get timestamps length from filename
        self.timestamp_length = len(re.match(pattern, self.name).groupdict()['period_end'])
        # Extract start and end dates from filename
        dates = get_start_end_dates_from_filename(filename=self.name,
                                                  pattern=pattern,
                                                  frequency=self.frequency,
                                                  calendar=self.calendar,
                                                  correction=self.correction)
        dates_num = date2num(dates, units=self.funits, calendar=self.calendar)
        # Apply time offset only if:
        # - NON-INSTANT axis
        # - AND NOT (frequency is 3hr or 6hr WITH corrected timestamps)
        if not self.is_instant and not (self.frequency in END_TIME_CORRECTION.keys() and not correction):
            dates_num += 0.5
        self.start_axis = dates_num[0]
        dates = num2date(dates_num, units=self.funits, calendar=self.calendar)
        self.start_num, self.end_num, _ = date2num(dates, units=self.tunits, calendar=self.calendar)
        self.start_date, self.end_date, _ = dates2str(list(dates))
        # Convert dates into timestamps
        self.start_timestamp, self.end_timestamp, _ = [
            truncated_timestamp(date, self.timestamp_length) for date in dates]
        # Declare last time attribute
        self.last_date = None
        self.last_timestamp = None
        self.last_num = None

    def load_last_date(self):
        """
        Builds the last theoretical date and timestamp.

        """
        num_axis = np.arange(start=self.start_axis,
                             stop=self.start_axis + self.length * self.step,
                             step=self.step)
        self.last_num = num_axis[-1]
        del num_axis
        try:
            last_date = num2date(self.last_num, units=self.funits, calendar=self.calendar)[0]
        except TypeError:
            last_date = num2date(self.last_num, units=self.funits, calendar=self.calendar)
        self.last_date = dates2str(last_date)
        # Convert dates into timestamps
        self.last_timestamp = truncated_timestamp(last_date, self.timestamp_length)
        self.last_num = date2num(last_date, units=self.tunits, calendar=self.calendar)

    def build_time_axis(self):
        """
        Rebuilds time axis from date axis, depending on MIP frequency, calendar and instant status.

        :returns: The corresponding theoretical time axis
        :rtype: *numpy.array*

        """
        num_axis = np.arange(start=self.start_axis,
                             stop=self.start_axis + self.length * self.step,
                             step=self.step, dtype=np.longdouble)
        date_axis = num2date(num_axis, units=self.funits, calendar=self.ref_calendar)
        del num_axis
        axis_rebuilt = date2num(date_axis, units=self.ref_units, calendar=self.ref_calendar)
        self.date_axis_rebuilt = dates2str(num2date(axis_rebuilt, units=self.ref_units, calendar=self.ref_calendar))
        return axis_rebuilt

    def build_time_bounds(self):
        """
        Rebuilds time boundaries from the start date, depending on MIP frequency, calendar and
        instant status.

        :returns: The corresponding theoretical time boundaries as a [n, 2] array
        :rtype: *numpy.array*

        """
        num_axis = np.arange(start=self.start_axis,
                             stop=self.start_axis + self.length * self.step,
                             step=self.step)
        num_axis_bnds_inf, num_axis_bnds_sup = num_axis, copy(num_axis)
        num_axis_bnds_inf -= 0.5 * self.step
        num_axis_bnds_sup += 0.5 * self.step
        num_axis_bnds = np.column_stack((num_axis_bnds_inf, num_axis_bnds_sup))
        del num_axis, num_axis_bnds_inf, num_axis_bnds_sup
        date_axis_bnds = num2date(num_axis_bnds, units=self.funits, calendar=self.ref_calendar)
        del num_axis_bnds
        axis_bnds_rebuilt = date2num(date_axis_bnds, units=self.ref_units, calendar=self.ref_calendar)
        self.date_bounds_rebuilt = np.column_stack((
            dates2str(num2date(axis_bnds_rebuilt[:, 0], units=self.ref_units, calendar=self.ref_calendar)),
            dates2str(num2date(axis_bnds_rebuilt[:, 1], units=self.ref_units, calendar=self.ref_calendar))
        ))
        return axis_bnds_rebuilt

    def nc_var_delete(self, variable):
        """
        Delete a NetCDF variable using NCO operators.
        A unique filename is generated to avoid multiprocessing errors.
        To overwrite the input file, the source file is dump using the ``cat`` Shell command-line
        to avoid Python memory limit.

        :param str variable: The variable to delete
        :raises Error: If the deletion failed

        """
        # Generate unique filename
        fftmp = '{}/{}{}'.format(self.directory, str(uuid4()), '.nc')
        try:
            nc = nco.Nco()
            nc.ncks(input=self.ffp,
                    output=fftmp,
                    options=['-x', '-O', '-v {}'.format(variable)])
            os.popen("cat {} > {}".format(fftmp, self.ffp), 'r')
            os.remove(fftmp)
        except:
            if os.path.exists(fftmp):
                os.remove(fftmp)
            raise NetCDFVariableRemoveFail(variable, self.ffp)

    def nc_att_delete(self, variable, attribute):
        """
        Delete a NetCDF dimension attribute using NCO operators.
        A unique filename is generated to avoid multiprocessing errors.
        To overwrite the input file, the source file is dump using the ``cat`` Shell command-line
        to avoid Python memory limit.

        :param str attribute: The attribute to delete
        :param str variable: The variable that has the attribute
        :raises Error: If the deletion failed

        """
        # Generate unique filename
        fftmp = '{}/{}{}'.format(self.directory, str(uuid4()), '.nc')
        try:
            nc = nco.Nco()
            nc.ncatted(input=self.ffp,
                       output=fftmp,
                       options='-a {},{},d,,'.format(attribute, variable))
            os.popen("cat {} > {}".format(fftmp, self.ffp), 'r')
            os.remove(fftmp)
        except:
            os.remove(fftmp)
            raise NetCDFAttributeRemoveFail(attribute, self.ffp, variable)

    def nc_var_overwrite(self, variable, data):
        """
        Rewrite variable to NetCDF file without copy.

        :param str variable: The variable to replace
        :param float array data: The data array to overwrite

        """
        with ncopen(self.ffp, 'r+') as nc:
            nc.variables[variable][:] = data

    def nc_att_overwrite(self, attribute, variable, data):
        """
        Rewrite attribute to NetCDF file without copy.

        :param str attribute: THe attribute to replace
        :param str variable: The variable that has the attribute
        :param str data: The string to add to overwrite

        """
        with ncopen(self.ffp, 'r+') as nc:
            setattr(nc.variables[variable], attribute, data)

    def nc_file_rename(self, new_filename):
        """
        Rename a NetCDF file.

        :param str new_filename: The new filename to apply

        """
        ffp = os.path.join(os.path.dirname(self.ffp), new_filename)
        if os.path.exists(ffp):
            raise RenamingNetCDFFailed(self.ffp, ffp, exists=True)
        try:
            os.rename(self.ffp, ffp)
        except OSError:
            raise RenamingNetCDFFailed(self.ffp, ffp)
        self.ffp = ffp
        self.filename = new_filename
