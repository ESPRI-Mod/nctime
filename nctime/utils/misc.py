#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Useful functions to use with this package.

"""

import logging
import os
import re
import sys
from ctypes import c_char_p
from multiprocessing import Value

from fuzzywuzzy import fuzz, process
from netCDF4 import Dataset
from netcdftime import datetime

from custom_exceptions import *


class ncopen(object):
    """
    Properly opens a netCDF file

    :param str path: The netCDF file full path
    :returns: The netCDF dataset object
    :rtype: *netCDF4.Dataset*

    """

    def __init__(self, path, mode='r'):
        self.path = path
        self.mode = mode
        self.nc = None

    def __enter__(self):
        try:
            self.nc = Dataset(self.path, self.mode)
        except IOError:
            raise InvalidNetCDFFile(self.path)
        return self.nc

    def __exit__(self, *exc):
        self.nc.close()


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


def match(pattern, string, inclusive=True):
    """
    Validates a string against a regular expression.
    Only match at the beginning of the string.
    Default is to match inclusive regex.

    :param str pattern: The regular expression to match
    :param str string: The string to test
    :param boolean inclusive: False if negative matching (i.e., exclude the regex)
    :returns: True if it matches
    :rtype: *boolean*

    """
    # Assert inclusive and exclusive flag are mutually exclusive
    if inclusive:
        return True if re.search(pattern, string) else False
    else:
        return True if not re.search(pattern, string) else False


def get_project(ffp):
    """
    Get project identifier from netCDF file.

    :param str ffp: The file full path
    :returns: The lower-case project id
    :rtype: *str*

    """
    project = None
    with ncopen(ffp) as nc:
        if 'mip_era' in nc.ncattrs():
            project = nc.getncattr('mip_era')
        elif 'project' in nc.ncattrs():
            project = nc.getncattr('project')
        else:
            key, score = process.extractOne('project', nc.ncattrs(), scorer=fuzz.partial_ratio)
            if score >= 80:
                project = nc.getncattr(key)
                logging.warning('Consider "{}" attribute instead of "project"'.format(key))
            else:
                raise NoNetCDFAttribute('project', ffp)
    return project.lower()


class ProcessContext(object):
    """
    Encapsulates the processing context/information for child process.

    :param dict args: Dictionary of argument to pass to child process
    :returns: The processing context
    :rtype: *ProcessContext*

    """

    def __init__(self, args):
        assert isinstance(args, dict)
        for key, value in args.items():
            setattr(self, key, value)


class Colors:
    """
    Background colors for print statements

    """

    def __init__(self):
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKGREEN = '\033[1;32m'
        self.WARNING = '\033[1;34m'
        self.FAIL = '\033[1;31m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'


COLORS = Colors()


class Print(object):
    """
    Class to manage and dispatch print statement depending on log and debug mode.

    """

    def __init__(self, log, debug, cmd, all):
        self._log = log
        self._debug = debug
        self._cmd = cmd
        self._all = all
        self._buffer = Value(c_char_p, '')
        self._colors = COLORS.__dict__
        logname = 'nctime-{}-{}.log'.format(self._cmd,
                                            datetime(1, 1, 1)._to_real_datetime().now().strftime("%Y%m%d-%H%M%S"))
        if self._log:
            if not os.path.isdir(self._log):
                os.makedirs(self._log)
            self._logfile = os.path.join(self._log, logname)
        else:
            self._logfile = os.path.join(os.getcwd(), logname)

    @staticmethod
    def print_to_stdout(msg):
        sys.stdout.write(msg)
        sys.stdout.flush()

    def print_to_logfile(self, msg):
        with open(self._logfile, 'a+') as f:
            for color in self._colors.values():
                msg = msg.replace(color, '')
            f.write(msg)

    def progress(self, msg):
        if self._log:
            self.print_to_stdout(msg)
        elif not self._debug:
            self.print_to_stdout(msg)

    def command(self, msg):
        if self._log:
            self.print_to_logfile(msg)
        elif self._debug:
            self.print_to_stdout(msg)

    def summary(self, msg):
        if self._log:
            self.print_to_stdout(msg)
            self.print_to_logfile(msg)
        else:
            self.print_to_stdout(msg)

    def info(self, msg):
        if self._log:
            self.print_to_stdout(msg)

    def debug(self, msg):
        if self._debug:
            if self._log:
                self.print_to_logfile(msg)
            else:
                self.print_to_stdout(msg)

    def warning(self, msg):
        if self._log:
            self.print_to_logfile(msg)
        elif self._debug:
            self.print_to_stdout(msg)
        else:
            self.print_to_stdout(msg)

    def error(self, msg, buffer=False):
        if self._log:
            self.print_to_logfile(msg)
        elif self._debug:
            self.print_to_stdout(msg)
        elif buffer:
            self._buffer.value += msg
        else:
            self.print_to_stdout(msg)

    def success(self, msg, buffer=False):
        if self._all:
            if self._log:
                self.print_to_logfile(msg)
            elif self._debug:
                self.print_to_stdout(msg)
            elif buffer:
                self._buffer.value += msg
            else:
                self.print_to_stdout(msg)

    def flush(self):
        if self._buffer.value:
            self._buffer.value = '\n' + self._buffer.value
            if self._log:
                self.print_to_logfile(self._buffer.value)
            else:
                self.print_to_stdout(self._buffer.value)
