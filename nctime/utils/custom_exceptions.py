#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""

from constants import FREQ_INC, TIME_UNITS, RUN_CARD, CONF_CARD


###############################
# Exceptions for NetCDF files #
###############################


class InvalidNetCDFFile(Exception):
    """
    Raised when not a NetCDF file.

    """

    def __init__(self, path):
        self.msg = "Invalid or corrupted NetCDF file."
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class RenamingNetCDFFailed(Exception):
    """
    Raised when NetCDF renaming failed.

    """

    def __init__(self, src, dst, exists=False):
        self.msg = "Cannot rename NetCDF file."
        if exists:
            self.msg = "NetCDF file already exists."
        self.msg += "\n<src: '{}'>".format(src)
        self.msg += "\n<dst: '{}'>".format(dst)

        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path, variable=None):
        self.msg = "Attribute not found"
        self.msg += "\n<attribute: '{}'>".format(attribute)
        if variable:
            self.msg += "\n<variable: '{}'>".format(variable)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "Variable not found"
        self.msg += "\n<variable: '{}'>".format(variable)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NetCDFTimeStepNotFound(Exception):
    """
    Raised when a NetCDF time index is not found.

    """

    def __init__(self, value, path):
        self.msg = "Time value not found"
        self.msg = "\n<value: '{}'>".format(value)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class EmptyTimeAxis(Exception):
    """
    Raised when a NetCDF time axis is empty.

    """

    def __init__(self, path):
        self.msg = "Empty time axis"
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


############################
# Miscellaneous exceptions #
############################

class InvalidFrequency(Exception):
    """
    Raised when frequency is unknown.

    """

    def __init__(self, frequency):
        self.msg = "Unknown frequency"
        self.msg += "\n<frequency: {}>".format(frequency)
        self.msg += "\n<available frequencies: {}>".format(', '.join(FREQ_INC.keys()))
        super(self.__class__, self).__init__(self.msg)


class InvalidUnits(Exception):
    """
    Raised when time units is unknown.

    """

    def __init__(self, units):
        allowed_units = ['{} ({})'.format(u[0], u[1]) for u in zip(TIME_UNITS.keys(), TIME_UNITS.values())]
        self.msg = "Unknown units"
        self.msg += "\n<units: {}>".format(units)
        self.msg += "\n<available units: {}>".format(', '.join(allowed_units))
        super(self.__class__, self).__init__(self.msg)


class NoFileFound(Exception):
    """
    Raised when frequency no file found.

    """

    def __init__(self, paths):
        self.msg = "No file found"
        for path in paths:
            self.msg += "\n<directory: {}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoRunCardFound(Exception):
    """
    Raised when no file patterns found in filedef.

    """

    def __init__(self, path):
        self.msg = "No {} found".format(RUN_CARD)
        self.msg += "\n<path: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigCardFound(Exception):
    """
    Raised when no file patterns found in filedef.

    """

    def __init__(self, path):
        self.msg = "No {} found".format(CONF_CARD)
        self.msg += "\n<path: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)
