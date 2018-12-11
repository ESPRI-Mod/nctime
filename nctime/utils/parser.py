#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class and methods used to parse command-line arguments.

"""

import os
import re
import sys
from argparse import RawTextHelpFormatter, ArgumentTypeError, Action, ArgumentParser
from gettext import gettext

from netcdftime import utime

from constants import TIME_UNITS, FREQ_INC, CALENDARS, TIME_UNITS_FORMAT
from custom_exceptions import InvalidUnits, InvalidFrequency, InvalidTable


class CustomArgumentParser(ArgumentParser):
    def error(self, message):
        """
        Overwrite the original method to change exist status.

        """
        self.print_usage(sys.stderr)
        self.exit(-1, gettext('%s: error: %s\n') % (self.prog, message))


class MultilineFormatter(RawTextHelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __init__(self, prog, default_columns=120):
        # Overload the HelpFormatter class.
        try:
            rows, columns = os.popen('stty size', 'r').read().split()
        except ValueError:
            rows, columns = 120, 120
            # stty fails if stdin is not a terminal.
            # But also check stdout, so that when writing to a file
            # behaviour is independent of terminal device.
            if sys.stdin.isatty() and sys.stdout.isatty():
                try:
                    _, columns = os.popen('stty size', 'r').read().split()
                except ValueError:
                    columns = default_columns
            else:
                columns = default_columns
        super(MultilineFormatter, self).__init__(prog, max_help_position=100, width=int(columns))


class DirectoryChecker(Action):
    """
    Custom action class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, list):
            checked_vals = [self.directory_checker(x) for x in values]
        else:
            checked_vals = self.directory_checker(values)
        setattr(namespace, self.dest, checked_vals)

    @staticmethod
    def directory_checker(path):
        """
        Checks if the supplied directory exists. The path is normalized without trailing slash.

        :param str path: The path list to check
        :returns: The same path list
        :rtype: *str*
        :raises Error: If one of the directory does not exist

        """
        path = os.path.abspath(os.path.normpath(path))
        if not os.path.isdir(path):
            msg = 'No such directory: {}'.format(path)
            raise ArgumentTypeError(msg)
        return path


class InputChecker(Action):
    """
    Checks if the supplied input exists.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        checked_values = [self.input_checker(x) for x in values]
        setattr(namespace, self.dest, checked_values)

    @staticmethod
    def input_checker(path):
        path = os.path.abspath(os.path.normpath(path))
        if not os.path.exists(path):
            msg = 'No such input: {}'.format(path)
            raise ArgumentTypeError(msg)
        return path


class CodeChecker(Action):
    """
    Checks if the supplied input exists.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        checked_values = self.code_checker(values)
        setattr(namespace, self.dest, checked_values)

    @staticmethod
    def code_checker(codes):
        allowed_codes = [str(x).rjust(3, '0') for x in range(0, 9)]
        if not isinstance(codes, str):
            msg = 'Type not supported: {} -- Should be a comma-separated string without spaces.'.format(codes)
            raise ArgumentTypeError(msg)
        codes = codes.split(',')
        for code in codes:
            if code not in allowed_codes:
                msg = 'Invalid code: {} -- Available codes are {}'.format(code, ', '.join(allowed_codes))
                raise ArgumentTypeError(msg)
        return codes


class TimestampChecker(Action):
    """
    Checks if the supplied timestamp is valid.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        checked_values = self.timestamp_checker(values)
        setattr(namespace, self.dest, checked_values)

    @staticmethod
    def timestamp_checker(timestamp):
        if not timestamp.isdigit():
            msg = 'Bad timestamp format -- Digits only (e.g.: YYYYMMDDmmhhss).'
            raise ArgumentTypeError(msg)
        return timestamp


class CalendarChecker(Action):
    """
    Checks if the supplied calendar is valid.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        checked_values = self.calendar_checker(values)
        setattr(namespace, self.dest, checked_values)

    @staticmethod
    def calendar_checker(calendar):
        if calendar not in CALENDARS:
            msg = 'Invalid calendar - Available calendars are {}'.format(', '.join(CALENDARS))
            raise ArgumentTypeError(msg)
        return calendar


class TimeUnitsChecker(Action):
    """
    Checks if the supplied time units has valid format.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        checked_values = self.units_checker(values)
        setattr(namespace, self.dest, checked_values)

    @staticmethod
    def units_checker(units):
        try:
            u = utime(units)
            return u.unit_string
        except ValueError, TypeError:
            msg = 'Invalid time units format - Available format is "{}"'.format(TIME_UNITS_FORMAT)
            raise ArgumentTypeError(msg)


def regex_validator(string):
    """
    Validates a Python regular expression syntax.

    :param str string: The string to check
    :returns: The Python regex
    :rtype: *re.compile*
    :raises Error: If invalid regular expression

    """
    try:
        return re.compile(string)
    except re.error:
        msg = 'Bad regex syntax: {}'.format(string)
        raise ArgumentTypeError(msg)


def positive_only(value):
    """
    Validates a positive number.

    :param str value: The value submitted
    :return:
    """
    value = int(value)
    if value < 0:
        msg = 'Invalid number. Should be a positive integer.'
        raise ArgumentTypeError(msg)
    return value


def processes_validator(value):
    """
    Validates the max processes number.

    :param str value: The max processes number submitted
    :return:
    """
    pnum = int(value)
    if pnum < 1 and pnum != -1:
        msg = 'Invalid processes number. Should be a positive integer or "-1".'
        raise ArgumentTypeError(msg)
    if pnum == -1:
        # Max processes = None corresponds to cpu.count() in Pool creation
        return None
    else:
        return pnum


def inc_converter(string):
    """
    Checks the increment value syntax.

    :param str string: The string to check
    :returns: The key/value tuple
    :rtype: *list*
    :raises Error: If invalid pair syntax

    """
    pattern = re.compile(r'([^=]+):([^=]+)=([^=]+)(?:,|$)')
    if not pattern.search(string):
        msg = 'Bad argument syntax: {}'.format(string)
        raise ArgumentTypeError(msg)
    else:
        table, frequency, v = pattern.search(string).groups()
        inc, units = v[:-1], v[-1]
        if not inc.isdigit():
            msg = 'Bad argument syntax -- only digits allowed: {}'.format(inc)
            raise ArgumentTypeError(msg)
        tables = set(zip(*FREQ_INC.keys())[0])
        tables.add('all')
        if table not in tables:
            raise InvalidTable(table)
        frequencies = set(zip(*FREQ_INC.keys())[1])
        frequencies.add('all')
        if frequency not in frequencies:
            raise InvalidFrequency(frequency)
        if units not in TIME_UNITS.keys():
            raise InvalidUnits(units)
        return table, frequency, inc, TIME_UNITS[units]


def table_inc_converter(pair):
    """
    Checks the key value syntax.

    :param str pair: The key/value pair to check
    :returns: The key/value pair
    :rtype: *list*
    :raises Error: If invalid pair syntax

    """
    pattern = re.compile(r'([^=]+)=([^=]+)(?:,|$)')
    if not pattern.search(pair):
        msg = 'Bad argument syntax: {}'.format(pair)
        raise ArgumentTypeError(msg)
    else:
        table, v = pattern.search(pair).groups()
        inc, units = v[:-1], v[-1]
        if not inc.isdigit():
            msg = 'Bad argument syntax -- only digits allowed: {}'.format(inc)
            raise ArgumentTypeError(msg)
        if table not in TABLE_INC.keys():
            raise InvalidTable(table)
        if units not in TIME_UNITS.keys():
            raise InvalidUnits(units)
        return table, inc, TIME_UNITS[units]
