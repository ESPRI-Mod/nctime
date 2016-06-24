#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Useful functions to use with timeaxis module.

"""

import os
import logging
import textwrap
import ConfigParser
from argparse import HelpFormatter
from datetime import datetime
from netCDF4 import date2num, num2date
from netcdftime import utime
import numpy as np
from netcdftime import datetime as phony_datetime


class MultilineFormatter(HelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """
    def __init__(self, prog):
        # Overload the HelpFormatter class.
        super(MultilineFormatter, self).__init__(prog, max_help_position=60, width=100)

    def _fill_text(self, text, width, indent):
        # Rewrites the _fill_text method to support multiline description.
        text = self._whitespace_matcher.sub(' ', text).strip()
        multiline_text = ''
        paragraphs = text.split('|n|n ')
        for paragraph in paragraphs:
            lines = paragraph.split('|n ')
            for line in lines:
                formatted_line = textwrap.fill(line, width,
                                               initial_indent=indent,
                                               subsequent_indent=indent) + '\n'
                multiline_text = multiline_text + formatted_line
            multiline_text += '\n'
        return multiline_text

    def _split_lines(self, text, width):
        # Rewrites the _split_lines method to support multiline helps.
        text = self._whitespace_matcher.sub(' ', text).strip()
        lines = text.split('|n ')
        multiline_text = []
        for line in lines:
            multiline_text.append(textwrap.fill(line, width))
        multiline_text[-1] += '\n'
        return multiline_text


def init_logging(logdir, level='INFO'):
    """
    Initiates the logging configuration (output, message formatting).
    In the case of a logfile, the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``

    :param str logdir: The relative or absolute logfile directory. If ``None`` the standard output is used.
    :param str level: The log level.

    """
    __LOG_LEVELS__ = {'CRITICAL': logging.CRITICAL,
                      'ERROR': logging.ERROR,
                      'WARNING': logging.WARNING,
                      'INFO': logging.INFO,
                      'DEBUG': logging.DEBUG,
                      'NOTSET': logging.NOTSET}
    if logdir:
        logfile = 'timeaxis-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"),
                                                os.getpid())
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
        logging.basicConfig(filename=os.path.join(logdir, logfile),
                            level=__LOG_LEVELS__[level],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=__LOG_LEVELS__[level],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')


def check_directory(path):
    """
    Checks if the supplied directory exists. The path is normalized before without trailing slash.

    :param list path: The path to check
    :returns: The same path if exists
    :rtype: *str*
    :raises Error: If the directory does not exist

    """
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise Exception('No such directory: {0}'.format(directory))
    return directory


def config_parse(config_path):
    """
    Parses the configuration file if exists.

    :param str config_path: The absolute or relative path of the configuration file
    :returns: The configuration file parser
    :rtype: *dict*
    :raises Error: If no configuration file exists
    :raises Error: If the configuration file parsing fails

    """
    if not os.path.isfile(config_path):
        raise Exception('Configuration file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_path)
    if not cfg:
        raise Exception('Configuration file parsing failed')
    return cfg


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
        return (timestamp+'0101').ljust(14, '0')
    elif len(timestamp) == 6:
        # Start month at first day
        return (timestamp+'01').ljust(14, '0')
    else:
        return timestamp.ljust(14, '0')


def _num2date(num_axis, units, calendar):
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
        return num2date(num_axis, units=units, calendar=calendar)
    else:
        # Return to time reference with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert the time reference 'units_as_days' as datetime object
        start_date = num2date(0.0, units=units_as_days, calendar=calendar)
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
                                  for years_to_add in np.arange(min_years, max_years+2)])
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
            return num2date(num_axis_mod_days, units=units_as_days, calendar=calendar)
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.floor(np.max(num_axis_mod)) + 1
            min_months = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, months_to_add)
                                   for months_to_add in np.arange(min_months, max_months+12)])
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
            return num2date(num_axis_mod_days, units=units_as_days, calendar=calendar)


def _date2num(date_axis, units, calendar):
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
        return date2num(date_axis, units=units, calendar=calendar)
    else:
        # Return to time reference with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert date axis as number of days since time reference
        days_axis = date2num(date_axis, units=units_as_days, calendar=calendar)
        # Convert the time reference 'units_as_days' as datetime object
        start_date = num2date(0.0, units=units_as_days, calendar=calendar)
        # Create years axis from input date axis
        years = np.array([date.year for date in np.atleast_1d(np.array(date_axis))])
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering
            # the whole 'num_axis' period
            max_years = np.max(years - start_date.year) + 1
            min_years = np.min(years - start_date.year) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([add_year(start_date, yid)
                                  for yid in np.arange(min_years, max_years+2)])
            # Convert years axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            years_axis_as_days = cdftime.date2num(years_axis)
            # Find closest index for years_axis_as_days in days_axis
            closest_index = np.searchsorted(years_axis_as_days, days_axis)
            # ???
            num = days_axis - years_axis_as_days[closest_index]
            den = np.diff(years_axis_as_days)[closest_index]
            return min_years + closest_index + num / den
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.max(12 * (years - start_date.year)) + 1
            min_months = np.min(12 * (years - start_date.year)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, mid)
                                   for mid in np.arange(min_months, max_months+12)])
            # Convert months axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            months_axis_as_days = cdftime.date2num(months_axis)
            # Find closest index for months_axis_as_days in days_axis
            closest_index = np.searchsorted(months_axis_as_days, days_axis)
            # ???
            num = days_axis - months_axis_as_days[closest_index]
            den = np.diff(months_axis_as_days)[closest_index]
            return min_months + closest_index + num / den


def add_month(date, months_to_add):
    """
    Finds the next month from date.

    :param datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int months_to_add: The number of months to add to the date
    :returns: The final date
    :rtype: *datetime*

    """
    years_to_add = int((date.month+months_to_add - np.mod(date.month+months_to_add - 1, 12) - 1) / 12)
    new_month = int(np.mod(date.month+months_to_add - 1, 12)) + 1
    new_year = date.year + years_to_add
    date_next = phony_datetime(year=new_year,
                               month=new_month,
                               day=date.day,
                               hour=date.hour,
                               minute=date.minute,
                               second=date.second)

    return date_next


def add_year(date, years_to_add):
    """
    Finds the next year from date.

    :param datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int years_to_add: The number of years to add to the date
    :returns: The final date
    :rtype: *datetime*

    """
    new_year = date.year + years_to_add
    date_next = phony_datetime(year=new_year,
                               month=date.month,
                               day=date.day,
                               hour=date.hour,
                               minute=date.minute,
                               second=date.second)
    return date_next


def date_print(date):
    """
    Prints date in format: %Y%m%d %H:%M:%s.

    :param datetime date: Accepts datetime or phony datetime objects
    :returns: The corresponding formatted date to print
    :rtype: *str*

    """
    return '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(date.year,
                                                                    date.month,
                                                                    date.day,
                                                                    date.hour,
                                                                    date.minute,
                                                                    date.second)


def trunc(f, n):
    """
    Truncates a float f to n decimal places before rounding

    :param float f: The number to truncates
    :param int n: Decimal number to place before rounding
    :returns: The corresponding truncated number
    :rtype: *float*

    """
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])
