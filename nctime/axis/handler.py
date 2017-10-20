#!/usr/bin/env python
"""
.. module:: nctime.axis.handler.py
   :platform: Unix
   :synopsis: File handler for time axis.

"""

import os
import re
from uuid import uuid4

import nco
import netCDF4
import numpy as np

from custom_exceptions import *
from nctime.utils.custom_exceptions import *
from nctime.utils.time import truncated_timestamp, get_start_end_dates_from_filename, dates2str, num2date, date2num


class File(object):
    """
    Handler providing methods to deal with file processing.

    :returns: The axis status
    :rtype: *File*

    """

    def __init__(self, ffp, has_bounds):
        self.ffp = ffp
        # Retrieve directory and filename full path
        self.directory, self.filename = os.path.split(ffp)
        # Start/end period dates from filename + next/last expected dates
        self.start_date = None
        self.end_date = None
        self.next_date = None
        self.last_date = None
        # Filename timestamp length
        self.timestamp_length = None
        # Start/end period timestamp from filename + next/last expected timestamps
        self.start_timestamp = None
        self.end_timestamp = None
        self.next_timestamp = None
        self.last_timestamp = None
        # Get time axis length
        try:
            f = netCDF4.Dataset(self.ffp, 'r')
        except IOError:
            raise InvalidNetCDFFile(self.ffp)
        self.length = f.variables['time'].shape[0]
        # Get time boundaries
        if has_bounds:
            self.time_bounds = f.variables['time_bnds'][:, :]
        else:
            self.time_bounds = None
        # Get time axis
        self.time_axis = f.variables['time'][:]
        # Get time units from file
        self.time_units = f.variables['time'].units
        # Get calendar from file
        self.calendar = f.variables['time'].calendar
        f.close()
        self.time_axis_rebuilt = None
        self.time_bounds_rebuilt = None
        self.status = list()
        self.new_checksum = None

    def get_start_end_dates(self, pattern, frequency, units, calendar):
        """
        Wraps and records :func:`get_start_end_dates_from_filename` results.

        :param re Object pattern: The filename pattern as a regex (from `re library \
        <https://docs.python.org/2/library/re.html>`_).
        :param str frequency: The time frequency
        :param str units: The proper time units
        :param str calendar: The NetCDF calendar attribute
        :returns: Start and end dates as number of days since the referenced date
        :rtype: *float*

        """
        self.timestamp_length = len(re.match(pattern, self.filename).groupdict()['period_end'])
        dates = get_start_end_dates_from_filename(filename=self.filename,
                                                  pattern=pattern,
                                                  frequency=frequency,
                                                  calendar=calendar)
        self.start_date, self.end_date, self.next_date = dates2str(dates)
        self.start_timestamp, self.end_timestamp, self.next_timestamp = [
            truncated_timestamp(date, self.timestamp_length) for date in dates]
        return date2num(dates, units=units, calendar=calendar)

    def checksum(self, checksum_type):
        """
        Does the checksum by the Shell avoiding Python memory limits.

        :param str checksum_type: Checksum type
        :returns: The checksum
        :rtype: *str*
        :raises Error: If the checksum fails

        """
        checksum_client = {'SHA256': 'sha256sum',
                           'MD5': 'md5sum'}
        assert (checksum_type in checksum_client.keys()), 'Invalid checksum type'
        try:
            shell = os.popen("{} {} | awk -F ' ' '{{ print $1 }}'".format(checksum_client[checksum_type],
                                                                          self.ffp),
                             'r')
            return shell.readline()[:-1]
        except:
            raise ChecksumFail(checksum_type, self.ffp)

    def build_time_axis(self, start, inc, input_units, output_units, calendar, is_instant=False):
        """
        Rebuilds time axis from date axis, depending on MIP frequency, calendar and instant status.

        :param float start: The numerical date to start (from ``netCDF4.date2num`` or \
        :func:`nctime.utils.time.date2num`)
        :param int inc: The time incrementation
        :param input_units: The time units deduced from the frequency
        :param output_units: The time units from the file
        :param calendar: The time calendar fro NetCDF attributes
        :param boolean is_instant: True if instantaneous time axis
        :returns: The corresponding theoretical time axis
        :rtype: *numpy.array*

        """
        num_axis = np.arange(start=start, stop=start + self.length * inc, step=inc)
        if input_units.split(' ')[0] in ['years', 'months']:
            last_date = num2date(num_axis[-1], units=input_units, calendar=calendar)[0]
        else:
            last_date = num2date(num_axis[-1], units=input_units, calendar=calendar)
        self.last_date = dates2str(last_date)
        self.last_timestamp = truncated_timestamp(last_date, self.timestamp_length)
        if not is_instant:
            num_axis += 0.5 * inc
        date_axis = num2date(num_axis, units=input_units, calendar=calendar)
        return date2num(date_axis, units=output_units, calendar=calendar)

    def build_time_bounds(self, start, inc, input_units, output_units, calendar):
        """
        Rebuilds time boundaries from the start date, depending on MIP frequency, calendar and
        instant status.

        :param float start: The numerical date to start (from ``netCDF4.date2num`` or \
        :func:`nctime.utils.time.date2num`)
        :param int inc: The time incrementation
        :param input_units: The time units deduced from the frequency
        :param output_units: The time units from the file
        :param calendar: The time calendar fro NetCDF attributes

        :returns: The corresponding theoretical time boundaries as a [n, 2] array
        :rtype: *numpy.array*

        """
        num_axis_bnds = np.column_stack(((np.arange(start=start,
                                                    stop=start + self.length * inc,
                                                    step=inc)),
                                         (np.arange(start=start,
                                                    stop=start + (self.length + 1) * inc,
                                                    step=inc)[1:])))
        date_axis_bnds = num2date(num_axis_bnds, units=input_units, calendar=calendar)
        return date2num(date_axis_bnds, units=output_units, calendar=calendar)

    def nc_var_delete(self, variable):
        """
        Delete a NetCDF variable using NCO operators.
        A unique filename is generated to avoid multithreading errors.
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
                    options='-x -O -v {}'.format(variable))
            os.popen("cat {} > {}".format(fftmp, self.ffp), 'r')
            os.remove(fftmp)
        except:
            os.remove(fftmp)
            raise NetCDFVariableRemoveFail(variable, self.ffp)

    def nc_att_delete(self, variable, attribute):
        """
        Delete a NetCDF dimension attribute using NCO operators.
        A unique filename is generated to avoid multithreading errors.
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
        try:
            f = netCDF4.Dataset(self.ffp, 'r+')
        except IOError:
            raise InvalidNetCDFFile(self.ffp)
        f.variables[variable][:] = data
        f.close()

    def nc_att_overwrite(self, attribute, variable, data):
        """
        Rewrite attribute to NetCDF file without copy.


        :param str attribute: THe attribute to replace
        :param str variable: The variable that has the attribute
        :param str data: The string to add to overwrite

        """
        try:
            f = netCDF4.Dataset(self.ffp, 'r+')
        except IOError:
            raise InvalidNetCDFFile(self.ffp)
        setattr(f.variables[variable], attribute, data)
        f.close()

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
