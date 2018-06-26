#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class and methods used to parse command-line arguments.

"""

import os
import re
import sys
import textwrap
from argparse import HelpFormatter, ArgumentTypeError, Action, ArgumentParser
from gettext import gettext

from constants import TIME_UNITS, FREQ_INC
from custom_exceptions import InvalidUnits, InvalidFrequency


class _ArgumentParser(ArgumentParser):
    def error(self, message):
        """
        Overwrite the original method to change exist status.

        """
        self.print_usage(sys.stderr)
        self.exit(-1, gettext('%s: error: %s\n') % (self.prog, message))


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
                multiline_text += formatted_line
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


def keyval_converter(pair):
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
        frequency, v = pattern.search(pair).groups()
        inc, units = v[:-1], v[-1]
        if not inc.isdigit():
            msg = 'Bad argument syntax -- only digits allowed: {}'.format(inc)
            raise ArgumentTypeError(msg)
        if frequency not in FREQ_INC.keys():
            raise InvalidFrequency(frequency)
        if units not in TIME_UNITS.keys():
            raise InvalidUnits(units)
        return frequency, inc, TIME_UNITS[units]
