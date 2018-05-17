#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""

from constants import FREQ_INC


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


############################
# Miscellaneous exceptions #
############################

class ChecksumFail(Exception):
    """
    Raised when a checksum fails.

    """

    def __init__(self, path, checksum_type=None):
        self.msg = "Checksum failed"
        if checksum_type:
            self.msg += "\n<checksum type: '{}'>".format(checksum_type)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class InvalidFrequency(Exception):
    """
    Raised when frequency is unknown.

    """

    def __init__(self, frequency):
        self.msg = "Unknown frequency"
        self.msg += "\n<frequency: {}>".format(frequency)
        self.msg += "\n<available frequencies: {}>".format(FREQ_INC.keys())
        super(self.__class__, self).__init__(self.msg)
