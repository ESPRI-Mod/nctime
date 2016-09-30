#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Methods used to deal with NetCDF file time axis.

"""

import logging
import re

import netCDF4
import numpy as np
from netcdftime import datetime
from netcdftime import utime

from constants import *
from exceptions import *


class TimeInit(object):
    """
    Encapsulates the time properties from first file into processing context.
    These properties has to be used as reference for all file into the directory.

     * The calendar, the frequency and the realm are read from NetCDF global attributes and \
     use to detect instantaneous time axis,
     * The NetCDF time units attribute has to be unchanged in respect with CF convention and \
     archives designs.

    +-------------------+-------------+---------------------------------+
    | Attribute         | Type        | Description                     |
    +===================+=============+=================================+
    | *self*.calendar   | *str*       | NetCDF calendar attribute       |
    +-------------------+-------------+---------------------------------+
    | *self*.frequency  | *str*       | NetCDF frequency attribute      |
    +-------------------+-------------+---------------------------------+
    | *self*.realm      | *str*       | NetCDF modeling realm attribute |
    +-------------------+-------------+---------------------------------+
    | *self*.tunits     | *str*       | Time units from file            |
    +-------------------+-------------+---------------------------------+
    | *self*.funits     | *str*       | Time units from frequency       |
    +-------------------+-------------+---------------------------------+
    | *self*.is_instant | *boolean*   | True if instantaneous axis      |
    +-------------------+-------------+---------------------------------+
    | *self*.has_bounds | *boolean*   | True if require time bounds     |
    +-------------------+-------------+---------------------------------+

    :param ProcessingContext ctx: The processing context
    :raises Error: If NetCDF time units attribute is missing
    :raises Error: If NetCDF frequency attribute is missing
    :raises Error: If NetCDF realm attribute is missing
    :raises Error: If NetCDF calendar attribute is missing

    """

    def __init__(self, ctx):
        ref_path = '{directory}/{ref}'.format(**ctx.__dict__)
        try:
            nc = netCDF4.Dataset(ref_path, 'r')
        except IOError:
            raise InvalidNetCDFFile(ref_path)
        # Check required global attributes exist
        for attribute in REQUIRED_ATTRIBUTES:
            if attribute not in nc.ncattrs():
                raise NoNetCDFAttribute(attribute, ref_path)
        # Check time variable exists
        if 'time' not in nc.variables.keys():
            raise NoNetCDFVariable('time', ref_path)
        # Check required time attributes exist
        for attribute in REQUIRED_TIME_ATTRIBUTES:
            if attribute not in nc.variables['time'].ncattrs():
                raise NoNetCDFAttribute(attribute, ref_path, 'time')
        # Get realm
        if nc.project_id == 'CORDEX':
            self.realm = 'atmos'
        else:
            self.realm = nc.modeling_realm
        # Get frequency
        self.frequency = nc.frequency
        # Get time units (i.e., days since ...)
        self.tunits = self.control_time_units(nc.variables['time'].units, ctx.tunits_default)
        # Convert time units into frequency units (i.e., months/year/hours since ...)
        self.funits = self.convert_time_units(self.tunits, self.frequency)
        # Get calendar
        self.calendar = nc.variables['time'].calendar
        if self.calendar == 'standard' and nc.model_id == 'CMCC-CM':
            self.calendar = 'proleptic_gregorian'
        # Get boolean on instantaneous time axis
        if 'cell_methods' not in nc.variables[ctx.variable].ncattrs():
            raise NoNetCDFAttribute('cell_methods', ref_path, ctx.variable)
        self.is_instant = False
        if 'point' in nc.variables[ctx.variable].cell_methods.lower():
            self.is_instant = True
        # Get boolean on time boundaries
        self.has_bounds = False
        if 'time_bnds' in nc.variables.keys():
            self.has_bounds = True
        nc.close()

    @staticmethod
    def control_time_units(tunits, tunits_default=None):
        """
        Controls the time units format as at least "days since YYYY-MM-DD".
        The time units can be forced within configuration file using the ``time_units_default`` option.

        :param str tunits: The NetCDF time units string from file
        :param tunits_default: The default time units that should be used
        :returns: The appropriate time units string formatted and controlled depending on the project
        :rtype: *str*

        """
        units = tunits.split()
        units[0] = unicode('days')
        if len(units[2].split('-')) == 1:
            units[2] += '-{0}-{1}'.format('01', '01')
        elif len(units[2].split('-')) == 2:
            units[2] += '-{0}'.format('01')
        if tunits_default and ' '.join(units) != tunits_default:
            logging.warning('Invalid time units. Replace "{0}" by "{1}"'.format(' '.join(units), tunits_default))
            return tunits_default
        else:
            return ' '.join(units)

    @staticmethod
    def convert_time_units(tunits, frequency):
        """
        Converts default time units from file into time units using the MIP frequency.
        As en example, for a 3-hourly file, the time units "days since YYYY-MM-DD" becomes
        "hours since YYYY-MM-DD".

        :param str tunits: The NetCDF time units string from file
        :param str frequency: The time frequency
        :returns: The converted time units string
        :rtype: *str*

        """
        units = {'subhr': 'minutes',
                 '3hr':   'hours',
                 '6hr':   'hours',
                 'day':   'days',
                 'mon':   'months',
                 'yr':    'years'}
        return tunits.replace('days', units[frequency])


def untroncated_timestamp(timestamp):
    """
    Returns proper digits for yearly and monthly truncated timestamps.
    The dates from filename are filled with the 0 digit to reach 14 digits.
    Consequently, yearly dates starts at January 1st and monthly dates starts at first day
    of the month.

    :param str timestamp: A date string from a filename
    :returns: The filled timestamp
    :rtype: *str*

    """
    if len(timestamp) == 4:
        # Start year at january 1st
        return (timestamp + '0101').ljust(14, '0')
    elif len(timestamp) == 6:
        # Start month at first day
        return (timestamp + '01').ljust(14, '0')
    else:
        return timestamp.ljust(14, '0')


def num2date(num_axis, units, calendar):
    """
    A wrapper from ``netCDF4.num2date`` able to handle "years since" and "months since" units.
    If time units are not "years since" or "months since", calls usual ``netcdftime.num2date``.

    :param numpy.array num_axis: The numerical time axis following units
    :param str units: The proper time units
    :param str calendar: The NetCDF calendar attribute
    :returns: The corresponding date axis
    :rtype: *array*

    """
    if not units.split(' ')[0] in ['years', 'months']:
        # If units are not 'years' or 'months since', call usual netcdftime.num2date:
        return netCDF4.num2date(num_axis, units=units, calendar=calendar)
    else:
        # Return to time reference with 'days since'
        units_as_days = 'days ' + ' '.join(units.split(' ')[1:])
        # Convert the time reference 'units_as_days' as datetime object
        start_date = netCDF4.num2date(0.0, units=units_as_days, calendar=calendar)
        # Control num_axis to always get an Numpy array (even with a scalar)
        num_axis_mod = np.atleast_1d(np.array(num_axis))
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering
            # the whole 'num_axis' period
            max_years = np.floor(np.max(num_axis_mod)) + 1
            min_years = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([add_year(start_date, years_to_add)
                                   for years_to_add in np.arange(min_years, max_years + 2)])
            # Convert rebuilt years axis as 'number of days since'
            cdftime = utime(units_as_days, calendar=calendar)
            years_axis_as_days = cdftime.date2num(years_axis)
            # Index of each years
            yind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' adding the number of days since referenced time
            # with an half-increment (num_axis_mod - yind) = 0 or 0.5
            num_axis_mod_days = (years_axis_as_days[yind - int(min_years)] +
                                 (num_axis_mod - yind) *
                                 np.diff(years_axis_as_days)[yind - int(min_years)])
            # Convert result as date axis
            return netCDF4.num2date(num_axis_mod_days, units=units_as_days, calendar=calendar)
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.floor(np.max(num_axis_mod)) + 1
            min_months = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, months_to_add)
                                    for months_to_add in np.arange(min_months, max_months + 12)])
            # Convert rebuilt months axis as 'number of days since'
            cdftime = utime(units_as_days, calendar=calendar)
            months_axis_as_days = cdftime.date2num(months_axis)
            # Index of each months
            mind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' adding the number of days since referenced time
            # with an half-increment (num_axis_mod - mind) = 0 or 0.5
            num_axis_mod_days = (months_axis_as_days[mind - int(min_months)] +
                                 (num_axis_mod - mind) *
                                 np.diff(months_axis_as_days)[mind - int(min_months)])
            # Convert result as date axis
            return netCDF4.num2date(num_axis_mod_days, units=units_as_days, calendar=calendar)


def date2num(date_axis, units, calendar):
    """
    A wrapper from ``netCDF4.date2num`` able to handle "years since" and "months since" units.
    If time units are not "years since" or "months since" calls usual ``netcdftime.date2num``.

    :param numpy.array date_axis: The date axis following units
    :param str units: The proper time units
    :param str calendar: The NetCDF calendar attribute
    :returns: The corresponding numerical time axis
    :rtype: *array*

    """
    # date_axis is the date time axis incremented following units (i.e., by years, months, etc).
    if not units.split(' ')[0] in ['years', 'months']:
        # If units are not 'years' or 'months since', call usual netcdftime.date2num:
        return netCDF4.date2num(date_axis, units=units, calendar=calendar)
    else:
        # Return to time reference with 'days since'
        units_as_days = 'days ' + ' '.join(units.split(' ')[1:])
        # Convert date axis as number of days since time reference
        days_axis = netCDF4.date2num(date_axis, units=units_as_days, calendar=calendar)
        # Convert the time reference 'units_as_days' as datetime object
        start_date = netCDF4.num2date(0.0, units=units_as_days, calendar=calendar)
        # Create years axis from input date axis
        years = np.array([date.year for date in np.atleast_1d(np.array(date_axis))])
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering
            # the whole 'num_axis' period
            max_years = np.max(years - start_date.year + 1)
            min_years = np.min(years - start_date.year - 1)
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([add_year(start_date, yid)
                                   for yid in np.arange(min_years, max_years + 2)])
            # Convert years axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            years_axis_as_days = cdftime.date2num(years_axis)
            # Find closest index for years_axis_as_days in days_axis
            closest_index = np.searchsorted(years_axis_as_days, days_axis)
            # Compute the difference between closest value of year axis and start date, in number of days
            num = days_axis - years_axis_as_days[closest_index]
            # Number of days of the corresponding closest year
            den = np.diff(years_axis_as_days)[closest_index]
            return min_years + closest_index + num / den
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.max(12 * (years - start_date.year + 1))
            min_months = np.min(12 * (years - start_date.year - 1))
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, mid)
                                    for mid in np.arange(min_months, max_months)])
            # Convert months axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            months_axis_as_days = cdftime.date2num(months_axis)
            # Find closest index for months_axis_as_days in days_axis
            closest_index = np.searchsorted(months_axis_as_days, days_axis)
            # Compute the difference between closest value of months axis and start date, in number of days
            num = days_axis - months_axis_as_days[closest_index]
            # Number of days of the corresponding closest month
            den = np.diff(months_axis_as_days)[closest_index]
            return min_months + closest_index + num / den


def add_month(date, months_to_add):
    """
    Finds the next month from date.

    :param netcdftime.datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int months_to_add: The number of months to add to the date
    :returns: The final date
    :rtype: *netcdftime.datetime*

    """
    years_to_add = int((date.month + months_to_add - np.mod(date.month + months_to_add - 1, 12) - 1) / 12)
    new_month = int(np.mod(date.month + months_to_add - 1, 12)) + 1
    new_year = date.year + years_to_add
    date_next = datetime(year=new_year,
                         month=new_month,
                         day=date.day,
                         hour=date.hour,
                         minute=date.minute,
                         second=date.second)

    return date_next


def add_year(date, years_to_add):
    """
    Finds the next year from date.

    :param netcdftime.datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int years_to_add: The number of years to add to the date
    :returns: The final date
    :rtype: *netcdftime.datetime*

    """
    new_year = date.year + years_to_add
    date_next = datetime(year=new_year,
                         month=date.month,
                         day=date.day,
                         hour=date.hour,
                         minute=date.minute,
                         second=date.second)
    return date_next


def get_start_end_dates_from_filename(filename, pattern, frequency, calendar):
    """
    Returns datetime objects for start and end dates from the filename.
    To rebuild a proper time axis, the dates from filename are expected to set the first
    time boundary and not the middle of the time interval.

    :param str filename: The filename
    :param re Object pattern: The filename pattern as a regex (from `re library \
    <https://docs.python.org/2/library/re.html>`_).
    :param str frequency: The time frequency
    :param str calendar: The NetCDF calendar attribute
    :param boolean is_instant: True if instantaneous time axis
    :returns: ``datetime`` instances for start and end dates from the filename
    :rtype: *netcdftime.datetime*

    """
    dates = []
    date_as_since = None
    for key in ['start_period', 'end_period']:
        date = re.match(pattern, filename).groupdict()[key]
        digits = untroncated_timestamp(date)
        # Convert string digits to %Y-%m-%d %H:%M:%S format
        date_as_since = ''.join([''.join(triple) for triple in
                                 zip(digits[::2], digits[1::2], ['', '-', '-', ' ', ':', ':', ':'])])[:-1]
        # Use num2date to create netCDF4 datetime objects
        if frequency in ['3hr', '6hr']:
            # Fix on filename digits for 3hr and 6hr frequencies. 3hr (6hr) files always start
            # at 000000 end at 2100000 (180000) whether the time axis is instantaneous or not.
            dates.append(num2date(TIME_CORRECTION[frequency][key][digits[-6:]],
                                  units='days since ' + date_as_since,
                                  calendar=calendar))
            # if is_instant:
            #     dates.append(num2date(INSTANT_TIME_CORRECTION[frequency][key][digits[-6:]],
            #                           units='days since ' + date_as_since,
            #                           calendar=calendar))
            # else:
            #     dates.append(num2date(AVERAGED_TIME_CORRECTION[frequency][key][digits[-6:]],
            #                           units='days since ' + date_as_since,
            #                           calendar=calendar))
        else:
            dates.append(num2date(0.0, units='days since ' + date_as_since, calendar=calendar))
    # Append date next to the end date for overlap diagnostic
    try:
        dates.append(num2date(time_inc(frequency)[0],
                              units=time_inc(frequency)[1] + ' since ' + date_as_since,
                              calendar=calendar)[0])
    except TypeError:
        dates.append(num2date(time_inc(frequency)[0],
                              units=time_inc(frequency)[1] + ' since ' + date_as_since,
                              calendar=calendar))
    return dates


def time_inc(frequency):
    """
    Returns the time incrementation and time units depending on the MIP frequency.
    :param str frequency: The MIP frequency
    :returns: The corresponding time value and units
    :rtype: *list*
    """
    inc = {'subhr': [30, 'minutes'],
           '3hr':   [3, 'hours'],
           '6hr':   [6, 'hours'],
           'day':   [1, 'days'],
           'mon':   [1, 'months'],
           'yr':    [1, 'years']}
    return inc[frequency]


def dates2str(dates, sep=True):
    """
    Prints date in format: %Y%m%d %H:%M:%s.

    :param list dates: A list of datetime or phony datetime objects
    :param boolean sep: Print corresponding date with separators if True
    :returns: The corresponding formatted date to print
    :rtype: *str*

    """
    strdates = []
    for date in dates:
        if sep:
            strdates.append('{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(date.year,
                                                                                     date.month,
                                                                                     date.day,
                                                                                     date.hour,
                                                                                     date.minute,
                                                                                     date.second))
        else:
            strdates.append('{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}'.format(date.year,
                                                                                date.month,
                                                                                date.day,
                                                                                date.hour,
                                                                                date.minute,
                                                                                date.second))
    return strdates


def date2str(date, sep=True):
    """
    Prints date in format: %Y%m%d %H:%M:%s.

    :param netcdftime.datetime date: A datetime or phony datetime objects
    :param boolean sep: Print date with separators if True
    :returns: The corresponding formatted date to print
    :rtype: *str*

    """
    if sep:
        return '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(date.year,
                                                                        date.month,
                                                                        date.day,
                                                                        date.hour,
                                                                        date.minute,
                                                                        date.second)
    else:
        return '{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}'.format(date.year,
                                                                   date.month,
                                                                   date.day,
                                                                   date.hour,
                                                                   date.minute,
                                                                   date.second)
