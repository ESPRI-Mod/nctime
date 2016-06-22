#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: File handler for time axis.

"""

import os
import logging
import numpy as np
from uuid import uuid4
import nco
from netCDF4 import Dataset
from utils import untroncated_timestamp, _num2date, _date2num, date_print

# Filename date correction for 3hr and 6hr files
__HALF_HOUR__ = 0.125/6.0
__AVERAGED_TIME_CORRECTION__ = {'3hr': {0: {'000000': 0.0,
                                            '003000': -__HALF_HOUR__,
                                            '013000': -__HALF_HOUR__*3,
                                            '030000': -__HALF_HOUR__*6},
                                        1: {'210000': 0.0,
                                            '213000': -__HALF_HOUR__,
                                            '223000': -__HALF_HOUR__*3,
                                            '230000': -__HALF_HOUR__*4,
                                            '000000': -__HALF_HOUR__*6,
                                            '003000': -__HALF_HOUR__*7}},
                                '6hr': {0: {'000000': 0.0,
                                            '060000': -__HALF_HOUR__*12},
                                        1: {'180000': 0.0,
                                            '230000': -__HALF_HOUR__*10,
                                            '000000': -__HALF_HOUR__*12}}}

__INSTANT_TIME_CORRECTION__ = {'3hr': {0: {'000000': __HALF_HOUR__*6,
                                           '003000': __HALF_HOUR__*5,
                                           '013000': __HALF_HOUR__*3,
                                           '030000': 0.0},
                                       1: {'210000': __HALF_HOUR__*6,
                                           '213000': __HALF_HOUR__*5,
                                           '223000': __HALF_HOUR__*3,
                                           '230000': __HALF_HOUR__*2,
                                           '000000': 0.0,
                                           '003000': -__HALF_HOUR__}},
                               '6hr': {0: {'000000': __HALF_HOUR__*12,
                                           '060000': 0.0},
                                       1: {'180000': __HALF_HOUR__*12,
                                           '230000': __HALF_HOUR__*2,
                                           '000000': 0.0}}}


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
    | *self*.bnds      | *boolean* | True if time boundaries excpected and not mistaken |
    +------------------+-----------+---------------------------------------------------+
    | *self*.checksum  | *str*     | New checksum if modified file                     |
    +------------------+-----------+---------------------------------------------------+
    | *self*.axis      | *array*   | Theoretical time axis                             |
    +------------------+-----------+---------------------------------------------------+
    | *self*.time      | *array*   | Time axis from file                               |
    +------------------+-----------+---------------------------------------------------+

    :returns: The axis status
    :rtype: *dict*

    """
    def __init__(self, directory, filename, has_bounds):
        self.directory, self.filename = directory, filename
        # Retrieve file full path
        self.ffp = '{0}/{1}'.format(self.directory, self.filename)
        # Start/end period dates from filename
        self.start_date = None
        self.end_date = None
        self.last_date = None
        # Get time axis length
        f = Dataset(self.ffp, 'r')
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
        f.close()
        self.time_axis_rebuilt = None
        self.time_bounds_rebuilt = None
        self.status = list()
        self.new_checksum = None

    def get_start_end_dates(self, pattern, frequency, units, calendar, is_instant=False):
        """
        Returns datetime objects for start and end dates from the filename.
        To rebuild a proper time axis, the dates from filename are expected to set the first
        time boundary and not the middle of the time interval.

        :returns: ``datetime`` instances for start and end dates from the filename
        :rtype: *datetime.datetime*

        """
        dates = []
        for date in pattern.search(self.filename).groups()[-2:]:
            digits = untroncated_timestamp(date)
            # Convert string digits to %Y-%m-%d %H:%M:%S format
            date_as_since = ''.join([''.join(triple) for triple in
                                     zip(digits[::2], digits[1::2], ['', '-', '-', ' ', ':', ':', ':'])])[:-1]
            # Use num2date to create netCDF4 datetime objects
            if frequency in ['3hr', '6hr']:
                # Fix on filename digits for 3hr and 6hr frequencies. 3hr (6hr) files always start
                # at 000000 end at 2100000 (180000) whether the time axis is instantaneous or not.
                date_index = pattern.search(self.filename).groups()[-2:].index(date)
                if is_instant:
                    date_correction = __INSTANT_TIME_CORRECTION__[frequency][date_index][digits[-6:]]
                    dates.append(_num2date(date_correction,
                                           units='days since ' + date_as_since,
                                           calendar=calendar))
                else:
                    date_correction = __AVERAGED_TIME_CORRECTION__[frequency][date_index][digits[-6:]]
                    dates.append(_num2date(date_correction,
                                           units='days since ' + date_as_since,
                                           calendar=calendar))
            else:
                dates.append(_num2date(0.0, units='days since ' + date_as_since, calendar=calendar))
        self.start_date, self.end_date = date_print(dates[0]), date_print(dates[1])
        return _date2num(dates, units=units, calendar=calendar)

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
            shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client[checksum_type],
                                                                            self.ffp),
                             'r')
            return shell.readline()[:-1]
        except:
            msg = '{0} checksum failed for {1}'.format(checksum_type, self.ffp)
            logging.warning(msg)
            raise Exception(msg)

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
            raise Exception('Deleting "{0}" variable failed for {1}'.format(variable, self.filename))

    def nc_att_delete(self, variable, attribute):
        """
        Delete a NetCDF dimension attribute using NCO operators.
        A unique filename is generated to avoid multithreading errors.
        To overwrite the input file, the source file is dump using the ``cat`` Shell command-line
        to avoid Python memory limit.

        :param str variable: The variable to delete
        :raises Error: If the deletion failed

        """

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
            raise Exception('Deleting "{0}" attribute failed for {1}'.format(attribute, self.filename))

    def build_time_axis(self, start, inc, input_units, output_units, calendar, is_instant=False):
        """
        Rebuilds time axis from date axis, depending on MIP frequency, calendar and instant status.

        :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
        :returns: The corresponding theoretical time axis
        :rtype: *float array*

        """
        num_axis = np.arange(start=start, stop=start + self.length * inc, step=inc)
        if input_units.split(' ')[0] in ['years', 'months']:
            last_date = _num2date(num_axis[-1], units=input_units, calendar=calendar)[0]
        else:
            last_date = _num2date(num_axis[-1], units=input_units, calendar=calendar)
        self.last_date = date_print(last_date)
        if not is_instant:
            num_axis += 0.5 * inc
        date_axis = _num2date(num_axis, units=input_units, calendar=calendar)
        return _date2num(date_axis, units=output_units, calendar=calendar)

    def build_time_bounds(self, start, inc, input_units, output_units, calendar, is_instant=False):
        """
        Rebuilds time boundaries from the start date, depending on MIP frequency, calendar and
        instant status.

        :param float date: The numerical date to start (from ``netCDF4.date2num`` or :func:`Date2num`)
        :param int length: The time axis length (i.e., the timesteps number)
        :param int inc: The time incrementation (from :func:`time_inc`)
        :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance).

        :returns: The corresponding theoretical time boundaries
        :rtype: *[n, 2] array*

        """
        num_axis_bnds = np.column_stack(((np.arange(start=start,
                                                    stop=start + self.length * inc,
                                                    step=inc)),
                                         (np.arange(start=start,
                                                    stop=start + (self.length + 1) * inc,
                                                    step=inc)[1:])))
        date_axis_bnds = _num2date(num_axis_bnds, units=input_units, calendar=calendar)
        return _date2num(date_axis_bnds, units=output_units, calendar=calendar)

    def nc_var_overwrite(self, variable, data):
        """
        Rewrite axis to NetCDF file without copy.
        :param axis:
        :return:
        """
        f = Dataset(self.ffp, 'r+')
        f.variables[variable][:] = data
        f.close()


    def nc_att_overwrite(self, attribute, variable, data):
        """
        Rewrite axis to NetCDF file without copy.
        :param axis:
        :return:
        """
        f = Dataset(self.ffp, 'r+')
        f.variables[variable].__dict__[attribute] = data
        f.close()
