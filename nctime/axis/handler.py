#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: File handler for time axis.

"""

from copy import deepcopy as copy
from uuid import uuid4
import nco
import numpy as np
from fuzzywuzzy import fuzz, process
from constants import *
from custom_exceptions import *
from nctime.utils.constants import CLIM_SUFFIX, AVERAGE_CORRECTION_FREQ
from nctime.utils.custom_exceptions import *
from nctime.utils.custom_print import *
from nctime.utils.misc import ncopen
from nctime.utils.time import truncated_timestamp, get_start_end_dates_from_filename, dates2str, num2date, date2num, \
    control_time_units, trunc, time_inc, convert_time_units


class File(object):
    """
    Handler providing methods to deal with file processing.

    :returns: The file handler
    :rtype: *File*

    """

    def __init__(self, ffp, pattern, ref_units, ref_calendar, input_start_timestamp=None, input_end_timestamp=None):
        # Retrieve the file full path
        self.ffp = ffp
        # Retrieve the reference time units to use
        self.ref_units = ref_units
        # Retrieve the reference calendar to use
        self.ref_calendar = ref_calendar
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
        # Get table from file
        try:
            self.table = self.nc_att_get('table_id')
            # Extract MIP table from string if needed
            self.table = self.table.split(" ")[1]
        except IndexError:
            self.table = self.nc_att_get('table_id')
        except NoNetCDFAttribute:
            self.table = 'None'
        # Get frequency from file
        self.frequency = self.nc_att_get('frequency')
        # Get netCDF time properties
        with ncopen(self.ffp) as nc:
            # Get time length and vector
            if 'time' not in nc.variables.keys():
                raise NoNetCDFVariable('time', self.ffp)
            self.length = nc.variables['time'].shape[0]
            if self.length == 0:
                raise EmptyTimeAxis(self.ffp)
            t = nc.variables['time'][:]
            self.time_axis = trunc(t, NDECIMALS)
            self.date_axis = dates2str(num2date(t, units=self.ref_units, calendar=self.ref_calendar))
            # Get time boundaries
            self.has_bounds = False
            self.time_bounds = None
            self.date_bounds = None
            self.tbnds = None
            if 'bounds' in nc.variables['time'].ncattrs():
                self.has_bounds = True
                self.tbnds = nc.variables['time'].bounds
            if 'climatology' in nc.variables['time'].ncattrs():
                self.has_bounds = True
                self.tbnds = nc.variables['time'].climatology
            if self.tbnds:
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
            # Get boolean on climatology time axis
            self.is_climatology = False
            if 'climatology' in nc.variables['time'].ncattrs():
                self.is_climatology = True
        # Get time step increment from frequency and table
        self.step, self.step_units = time_inc(self.table, self.frequency)
        # Convert reference time units into frequency units depending on the file (i.e., months/year/hours since ...)
        self.funits = convert_time_units(self.ref_units, self.table, self.frequency)
        # Get timestamps length from filename
        self.timestamp_length = len(re.match(pattern, self.name).groupdict()['period_end'])
        # Overwrite filename timestamp if submitted
        # Extract start and end dates from filename
        dates = get_start_end_dates_from_filename(filename=self.name,
                                                  pattern=pattern,
                                                  table=self.table,
                                                  frequency=self.frequency,
                                                  calendar=self.calendar,
                                                  start=input_start_timestamp,
                                                  end=input_end_timestamp)
        dates_num = trunc(date2num(dates, units=self.funits, calendar=self.calendar), NDECIMALS)
        if self.is_climatology:
            # Apply time offset corresponding to the climatology:
            self.clim_diff = (dates_num[1] - dates_num[0]) / 2
            if self.frequency in ['monC', 'monClim']:
                dates_num[0] += self.clim_diff - 11
                dates_num[1] -= self.clim_diff
            elif self.frequency == '1hrCM':
                dates_num[0] += self.clim_diff - 23.5
                dates_num[1] -= self.clim_diff + 0.5
            else:
                raise InvalidClimatologyFrequency(self.frequency)
        elif not self.is_instant and self.frequency in AVERAGE_CORRECTION_FREQ:
            # Apply time offset for non-instant time axis:
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

    def get_last_date(self):
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
        assert len(num_axis) == self.length
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
        assert len(num_axis) == self.length
        num_axis_bnds_inf, num_axis_bnds_sup = num_axis, copy(num_axis)
        if self.is_climatology:
            if self.frequency in ['monC', 'monClim']:
                num_axis_bnds_inf -= self.clim_diff - 11
                num_axis_bnds_sup += self.clim_diff + 1
            elif self.frequency == '1hrCM':
                num_axis_bnds_inf -= self.clim_diff - 23.5
                num_axis_bnds_sup += self.clim_diff + 0.5
        else:
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
        try:
            nc = nco.Nco()
            nc.ncks(input=self.ffp,
                    options=['-O', '-x', '-v {}'.format(variable)])
        except:
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
        try:
            nc = nco.Nco()
            nc.ncatted(input=self.ffp,
                       options=['-O', '-a {},{},d,,'.format(attribute, variable)])
        except:
            raise NetCDFAttributeRemoveFail(attribute, self.ffp, variable)

    def nc_var_overwrite(self, variable, data):
        """
        Rewrite variable to NetCDF file without copy.

        :param str variable: The variable to replace
        :param float array data: The data array to overwrite

        """
        with ncopen(self.ffp, 'r+') as nc:
            nc.variables[variable][:] = data

    def nc_att_overwrite(self, attribute, data, variable=None):
        """
        Rewrite attribute to NetCDF file without copy.

        :param str attribute: The attribute to replace
        :param str data: The string to add to overwrite
        :param str variable: The variable that has the attribute, default is global attributes

        """
        with ncopen(self.ffp, 'r+') as nc:
            if variable:
                if variable not in nc.variables.keys():
                    raise NoNetCDFVariable(variable, nc.path)
                nc.variables[variable].setncattr(attribute, data)
            else:
                nc.setncattr(attribute, data)

    def nc_att_get(self, attribute, variable=None):
        """
        Get attribute from NetCDF file. Default is to find into global attributes.
        If attribute key is not found, get the closest key name instead.


        :param str attribute: The attribute key to get
        :param str variable: The variable from which to find the attribute. Global is None.
        :return: The attribute value
        :rtype: *str*

        """
        with ncopen(self.ffp) as nc:
            if variable:
                attrs = nc.variables[variable].__dict__
            else:
                attrs = nc.__dict__
            if attribute in attrs.keys():
                return attrs[attribute]
            else:
                key, score = process.extractOne(attribute, attrs, scorer=fuzz.partial_ratio)
                if score >= 80:
                    Print.warning('Consider "{}" attribute instead of "frequency"'.format(key))
                    return attrs(key)
                else:
                    raise NoNetCDFAttribute(attribute, self.ffp)

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
