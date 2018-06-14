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
from datetime import datetime as dt
from multiprocessing import Value

from fuzzywuzzy import fuzz, process
from netCDF4 import Dataset

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


class COLORS:
    """
    Background colors for print statements

    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[1;32m'
    WARNING = '\033[1;34m'
    FAIL = '\033[1;31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Print(object):
    """
    Class to manage and dispatch print statement depending on log and debug mode.

    """
    LOG = None
    DEBUG = False
    ALL = False
    CMD = None
    BUFFER = Value(c_char_p, '')
    LOGFILE = None

    @staticmethod
    def init(log, debug, cmd, all):
        Print.LOG = log
        Print.DEBUG = debug
        Print.CMD = cmd
        Print.ALL = all
        logname = '{}-{}'.format(Print.CMD, dt.now().strftime("%Y%m%d-%H%M%S"))
        if Print.LOG:
            logdir = Print.LOG
            if not os.path.isdir(Print.LOG):
                os.makedirs(Print.LOG)
        else:
            logdir = os.getcwd()
        Print.LOGFILE = os.path.join(logdir, logname + '.log')

    @staticmethod
    def print_to_stdout(msg):
        sys.stdout.write(msg)
        sys.stdout.flush()

    @staticmethod
    def print_to_logfile(msg):
        with open(Print.LOGFILE, 'a+') as f:
            for color in COLORS.__dict__.values():
                msg = msg.replace(color, '')
            f.write(msg)

    @staticmethod
    def progress(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)
        elif not Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def command(msg):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def summary(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)
            Print.print_to_logfile(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def info(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)

    @staticmethod
    def debug(msg):
        if Print.DEBUG:
            if Print.LOG:
                Print.print_to_logfile(msg)
            else:
                Print.print_to_stdout(msg)

    @staticmethod
    def warning(msg):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def error(msg, buffer=False):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        elif buffer:
            Print.BUFFER.value += msg
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def success(msg, buffer=False):
        if Print.ALL:
            if Print.LOG:
                Print.print_to_logfile(msg)
            elif Print.DEBUG:
                Print.print_to_stdout(msg)
            elif buffer:
                Print.BUFFER.value += msg
            else:
                Print.print_to_stdout(msg)

    @staticmethod
    def flush():
        if Print.BUFFER.value:
            Print.BUFFER.value = '\n' + Print.BUFFER.value
            if Print.LOG:
                Print.print_to_logfile(Print.BUFFER.value)
            else:
                Print.print_to_stdout(Print.BUFFER.value)
