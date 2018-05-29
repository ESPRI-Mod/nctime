#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


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
