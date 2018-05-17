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
from netcdftime import utime

from constants import *
from custom_exceptions import *
from misc import ncopen


class TimeInit(object):
    """
    Encapsulates the time properties from first file into processing context.
    These properties has to be used as reference for all files into the directory.

     * The calendar, the frequency and the realm are read from NetCDF global attributes and \
     use to detect instantaneous time axis,
     * The NetCDF time units attribute has to be unchanged in respect with CF convention and \
     archives designs.

    :param str ref: The reference file full path
    :param str tunits_default: The default time units if exists
    :raises Error: If NetCDF time units attribute is missing
    :raises Error: If NetCDF frequency attribute is missing
    :raises Error: If NetCDF realm attribute is missing
    :raises Error: If NetCDF calendar attribute is missing

    """

    def __init__(self, ref, tunits_default=None):
        with ncopen(ref) as nc:
            # Check time variable exists
            if 'time' not in nc.variables.keys(): raise NoNetCDFVariable('time', ref)
            # Get reference time units
            if 'units' not in nc.variables['time'].ncattrs(): raise NoNetCDFAttribute('units', ref, 'time')
            self.tunits = control_time_units(nc.variables['time'].units, tunits_default)
            # Get reference calendar
            if 'calendar' not in nc.variables['time'].ncattrs(): raise NoNetCDFAttribute('calendar', ref, 'time')
            self.calendar = nc.variables['time'].calendar


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
        units[2] += '-{}-{}'.format('01', '01')
    elif len(units[2].split('-')) == 2:
        units[2] += '-{}'.format('01')
    if tunits_default and ' '.join(units) != tunits_default:
        logging.warning('Invalid time units. Replace "{}" by "{}"'.format(' '.join(units), tunits_default))
        return tunits_default
    else:
        return ' '.join(units)


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
    return tunits.replace('days', FREQ_INC[frequency][1])


def untruncated_timestamp(timestamp):
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


def truncated_timestamp(date, length):
    """
    Returns proper digits depending on datetime object.

    :param datetime.datetime date: Datetime or phony datetime object
    :param int length: The timestamp length expected
    :returns: The corresponding timestamp
    :rtype: *str*

    """
    timestamp = date2str(date, iso_format=False)
    return timestamp[:length]


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
    :returns: Start and end dates from the filename
    :rtype: *netcdftime.datetime*

    """
    dates = []
    date_as_since = None
    for key in ['period_start', 'period_end']:
        date = re.match(pattern, filename).groupdict()[key]
        digits = untruncated_timestamp(date)
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


def get_first_last_timesteps(ffp):
    """
    Returns first and last time steps from time axis of a NetCDF file.

    :param str ffp: The file full path
    :returns: The first and last timestep
    :rtype: *int*

    """
    with ncopen(ffp) as nc:
        if 'time' not in nc.variables.keys():
            raise NoNetCDFVariable('time', ffp)
        first = nc.variables['time'][0]
        last = nc.variables['time'][-1]
        return first, last


def get_next_timestep(ffp, current_timestep):
    """
    Returns next time step from time axis given the current one.

    :param str ffp: The file full path
    :param int current_timestep: The current_timestep
    :returns: The next timestep
    :rtype: *int*

    """
    with ncopen(ffp) as nc:
        if 'time' not in nc.variables.keys():
            raise NoNetCDFVariable('time', ffp)
        else:
            time = nc.variables['time'][:]
        try:
            index = int(np.where(time == current_timestep)[0][0])
        except IndexError:
            try:
                index = int(np.where(time == int(current_timestep))[0][0])
            except IndexError:
                raise NetCDFTimeStepNotFound(current_timestep, ffp)
        next_timestep = time[index + 1]
        del time
        return next_timestep


def time_inc(frequency):
    """
    Returns the time incrementation and time units depending on the MIP frequency.

    :param str frequency: The MIP frequency
    :returns: The corresponding time value and units
    :rtype: *list*

    """
    return FREQ_INC[frequency]


def dates2int(dates):
    """
    Converts (a list of) dates as integers.

    :param list dates: A list of datetime or phony datetime objects
    :returns: The corresponding formatted integers
    :rtype: *list* or *int*

    """
    if isinstance(dates, list):
        return map(int, dates2str(dates, iso_format=False))
    else:
        return int(dates2str(dates, iso_format=False))


def dates2str(dates, iso_format=True):
    """
    Converts (a list of) dates in format: %Y%m%d %H:%M:%s.

    :param netcdftime.datetime/list dates: A list of datetime or phony datetime objects
    :param boolean iso_format: ISO format date if True
    :returns: The corresponding formatted strings
    :rtype: *list* or *str*

    """
    if isinstance(dates, list):
        return [date2str(date, iso_format) for date in dates]
    else:
        return date2str(dates, iso_format)


def date2str(date, iso_format=True):
    """
    Converts date in format: %Y%m%d %H:%M:%s.

    :param netcdftime.datetime date: A datetime or phony datetime objects
    :param boolean iso_format: ISO format date if True
    :returns: The corresponding formatted string
    :rtype: *str*

    """
    if iso_format:
        return '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}'.format(date.year,
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


def ints2date(dates):
    """
    Converts (a list of) integer into corresponding datetime objects.

    :param list dates: A list of formatted integer
    :returns: The corresponding datetime objects
    :rtype: *list* or *netcdftime.datetime*

    """
    if isinstance(dates, list):
        dates = map(str, dates)
    else:
        dates = str(dates)
    return strs2date(dates, iso_format=False)


def strs2date(dates, iso_format=False):
    """
    Converts (a list of) formatted string %Y%m%d%H:%M:%s into corresponding datetime objects.

    :param list/str dates: A list of formatted dated
    :param boolean iso_format: ISO format date if True
    :returns: The corresponding datetime objects
    :rtype: *list* or *netcdftime.datetime*

    """
    if isinstance(dates, list):
        return [str2date(date, iso_format) for date in dates]
    else:
        return str2date(dates, iso_format)


def str2date(date, iso_format=True):
    """
    Converts a string format %Y%m%d%H:%M:%s into datetime object.

    :param str date: The formatted date
    :param boolean iso_format: ISO format date if True
    :returns: The corresponding datetime
    :rtype: *netcdftime.datetime*

    """
    if iso_format:
        pattern = re.compile(r'^(?P<year>\d{})-'
                             r'(?P<month>\d{2})-'
                             r'(?P<day>\d{2})T'
                             r'(?P<hour>\d{2}):'
                             r'(?P<minute>\d{2}):'
                             r'(?P<second>\d{2})$')
    else:
        pattern = re.compile(r'^(?P<year>\d{4})'
                             r'(?P<month>\d{2})'
                             r'(?P<day>\d{2})'
                             r'(?P<hour>\d{2})'
                             r'(?P<minute>\d{2})'
                             r'(?P<second>\d{2})$')
    attr = pattern.match(str(date)).groupdict()
    for k, v in attr.iteritems():
        attr[k] = int(v)
    return datetime(**attr)
