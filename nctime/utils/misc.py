#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Useful functions to use with this package.

"""

import logging
import os
import re

from netCDF4 import Dataset
from netcdftime import datetime
from fuzzywuzzy import fuzz, process

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


class LogFilter(logging.Filter):
    """
    Log filter with upper log level to use with the Python
    `logging <https://docs.python.org/2/library/logging.html>`_ module.

    """

    def __init__(self, level):
        self.level = level

    def filter(self, log_record):
        """
        Set the upper log level.

        """
        return log_record.levelno <= self.level


class NoColorFilter(logging.Filter):
    """
    Log filter with upper log level to use with the Python
    `logging <https://docs.python.org/2/library/logging.html>`_ module.

    """

    def filter(self, record):
        """
        Use filter to post-process log record and remove color patterns.
        Returns true in any case.

        """
        msg = record.msg
        color_pattern = re.compile('\[[0-9;]*m')
        found_patterns = re.findall(color_pattern, msg)
        if found_patterns:
            msg = re.sub(color_pattern, '', msg)
        record.msg = msg
        return True


def init_logging(log, level='INFO'):
    """
    Initiates the logging configuration (output, date/message formatting).
    If a directory is submitted the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``If ``None`` the standard output is used.

    :param str log: The logfile directory.
    :param str level: The log level.

    """
    logname = 'nctime-{}-{}'.format(datetime(1, 1, 1)._to_real_datetime().now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    formatter = logging.Formatter(fmt='%(message)s')
    if log:
        if not os.path.isdir(log):
            os.makedirs(log)
        logfile = os.path.join(log, logname)
    else:
        logfile = os.path.join(os.getcwd(), logname)
    logging.getLogger().setLevel(logging.DEBUG)
    if log:
        handler = logging.FileHandler(filename='{}.log'.format(logfile), delay=True)
        handler.addFilter(NoColorFilter())
    else:
        handler = logging.StreamHandler()
    handler.setLevel(logging.__dict__[level])
    handler.addFilter(LogFilter(logging.CRITICAL))
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


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
    with ncopen(ffp) as nc:
        if 'mip_era' in nc.ncattrs():
            project = nc.getncattr('mip_era')
        elif 'project' in nc.ncattrs():
            project = nc.getncattr('project')
        else:
            key, score = process.extractOne('project', nc.ncattrs(), scorer=fuzz.partial_ratio)
            if score >= 80:
                frequency = nc.getncattr(key)
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
