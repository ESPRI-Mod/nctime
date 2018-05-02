#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""

from hashlib import algorithms as checksum_types


############################
# Miscellaneous exceptions #
############################

class InvalidChecksumType(Exception):
    """
    Raised when checksum type in unknown.

    """

    def __init__(self, client):
        self.msg = "Checksum type not supported or invalid."
        self.msg += "\n<checksum type: '{}'>".format(client)
        self.msg += "\n<allowed algorithms: '{}'>".format(checksum_types)
        super(self.__class__, self).__init__(self.msg)


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


###############################
# Exceptions for NetCDF files #
###############################

class NetCDFVariableRemoveFail(Exception):
    """
    Raised when NetCDF variable removal fails.

    """

    def __init__(self, variable, path):
        self.msg = "Cannot remove variable: {}.".format(variable)
        self.msg += "\n<file: {}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NetCDFAttributeRemoveFail(Exception):
    """
    Raised when NetCDF attribute removal fails.

    """

    def __init__(self, attribute, path, variable=None):
        if variable:
            self.msg = "Cannot remove attribute: {}.".format(attribute)
            self.msg += "\n<variable: {}>".format(variable)
        else:
            self.msg = "Cannot remove global attribute: {}.".format(attribute)
        self.msg += "\n<file: {}>".format(path)
        super(self.__class__, self).__init__(self.msg)
