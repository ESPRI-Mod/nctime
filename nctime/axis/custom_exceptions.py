#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class ChecksumFail(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, checksum_type, path):
        self.msg = "{0} checksum failed.".format(checksum_type)
        self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NetCDFVariableRemoveFail(Exception):
    """
    Raised when NetCDF variable removal fails.

    """

    def __init__(self, variable, path):
        self.msg = "Cannot remove variable: {0}.".format(variable)
        self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NetCDFAttributeRemoveFail(Exception):
    """
    Raised when NetCDF attribute removal fails.

    """

    def __init__(self, attribute, path, variable=None):
        if variable:
            self.msg = "Cannot remove attribute: {0}.".format(attribute)
            self.msg += "\n<variable: {0}>".format(variable)
        else:
            self.msg = "Cannot remove global attribute: {0}.".format(attribute)
        self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)
