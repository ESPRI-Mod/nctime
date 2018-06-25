#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Useful functions to use with this package.

"""

import logging
import re

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
