#!/usr/bin/env python
"""
.. module:: nctime.axis.handler.py
   :platform: Unix
   :synopsis: File handler for time axis.

"""

import os
import gc
from uuid import uuid4

import nco
import netCDF4
import numpy as np

from exceptions import *
from nctime.utils import time
from nctime.utils.exceptions import *


class File(object):
    """
    Handler providing methods to deal with file processing.
    It encapsulates the following file diagnostic to print or save:

    +------------------+-----------+---------------------------------------------------+
    | Attribute        | Type      | Description                                       |
    +==================+===========+===================================================+
    | *self*.directory | *str*     | Variable to scan                                  |
    +------------------+-----------+---------------------------------------------------+
    | *self*.file      | *str*     | Filename                                          |
    +------------------+-----------+---------------------------------------------------+
    | *self*.start     | *str*     | Start date from filename                          |
    +------------------+-----------+---------------------------------------------------+
    | *self*.end       | *str*     | End date from filename                            |
    +------------------+-----------+---------------------------------------------------+
    | *self*.last      | *str*     | Last date from theoretical time axis              |
    +------------------+-----------+---------------------------------------------------+
    | *self*.steps     | *int*     | Time axis length                                  |
    +------------------+-----------+---------------------------------------------------+
    | *self*.instant   | *boolean* | True if instantaneous time axis                   |
    +------------------+-----------+---------------------------------------------------+
    | *self*.calendar  | *str*     | NetCDF calendar attribute                         |
    +------------------+-----------+---------------------------------------------------+
    | *self*.units     | *str*     | Expected time units                               |
    +------------------+-----------+---------------------------------------------------+
    | *self*.control   | *list*    | Errors status                                     |
    +------------------+-----------+---------------------------------------------------+
    | *self*.bnds      | *boolean* | True if time bounds excpected and not mistaken    |
    +------------------+-----------+---------------------------------------------------+
    | *self*.checksum  | *str*     | New checksum if modified file                     |
    +------------------+-----------+---------------------------------------------------+
    | *self*.axis      | *array*   | Theoretical time axis                             |
    +------------------+-----------+---------------------------------------------------+
    | *self*.time      | *array*   | Time axis from file                               |
    +------------------+-----------+---------------------------------------------------+

    :returns: The axis status
    :rtype: *File*

    """

    def __init__(self, directory, filename, has_bounds):
        self.directory, self.filename = directory, filename
        # Retrieve file full path
        self.ffp = os.path.join(self.directory, self.filename)
        # Start/end period dates from filename
        self.start_date = None
        self.end_date = None
        self.last_date = None
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
        f.close() ; del f ; gc.collect()
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
        dates = time.get_start_end_dates_from_filename(filename=self.filename,
                                                       pattern=pattern,
                                                       frequency=frequency,
                                                       calendar=calendar)
        self.start_date, self.end_date, _ = time.dates2str(dates)
        return time.date2num(dates, units=units, calendar=calendar)

    def checksum(self, checksum_type):
        """
        Does the checksum by the Shell avoiding Python memory limits.

        :param str checksum_type: Checksum type
        :returns: The checksum
        :rtype: *str*
        :raises Error: If the checksum fails

        """
        checksum_client = {'SHA256': 'sha256sum',
                           'MD5':    'md5sum'}
        assert (checksum_type in checksum_client.keys()), 'Invalid checksum type'
        try:
            shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client[checksum_type],
                                                                            self.ffp),
                             'r')
            return shell.readline()[:-1]
        except:
            raise ChecksumFail(checksum_type, self.ffp)

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
        fftmp = '{0}/{1}{2}'.format(self.directory, str(uuid4()), '.nc')
        try:
            nc = nco.Nco()
            nc.ncks(input=self.ffp,
                    output=fftmp,
                    options='-x -O -v {0}'.format(variable))
            os.popen("cat {0} > {1}".format(fftmp, self.ffp), 'r')
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
        fftmp = '{0}/{1}{2}'.format(self.directory, str(uuid4()), '.nc')
        try:
            nc = nco.Nco()
            nc.ncatted(input=self.ffp,
                       output=fftmp,
                       options='-a {0},{1},d,,'.format(attribute, variable))
            os.popen("cat {0} > {1}".format(fftmp, self.ffp), 'r')
            os.remove(fftmp)
        except:
            os.remove(fftmp)
            raise NetCDFAttributeRemoveFail(attribute, self.ffp, variable)

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
            last_date = time.num2date(num_axis[-1], units=input_units, calendar=calendar)[0]
        else:
            last_date = time.num2date(num_axis[-1], units=input_units, calendar=calendar)
        self.last_date = time.date2str(last_date)
        if not is_instant:
            num_axis += 0.5 * inc
        date_axis = time.num2date(num_axis, units=input_units, calendar=calendar)
        return time.date2num(date_axis, units=output_units, calendar=calendar)

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
        date_axis_bnds = time.num2date(num_axis_bnds, units=input_units, calendar=calendar)
        return time.date2num(date_axis_bnds, units=output_units, calendar=calendar)

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
