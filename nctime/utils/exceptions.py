#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""


class EmptyConfigFile(Exception):
    """
    Raised when configuration file is empty.

    """

    def __init__(self, paths):
        self.msg = "Empty configuration parser."
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigFile(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, path):
        self.msg = "No or not a file"
        self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigSection(Exception):
    """
    Raised when no corresponding section found in configuration file.

    """

    def __init__(self, section, paths):
        self.msg = "No section: '{0}'".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOption(Exception):
    """
    Raised when no corresponding option found in section of the configuration file.

    """

    def __init__(self, option, section, paths):
        self.msg = "No option: '{0}'".format(option)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigValue(Exception):
    """
    Raised when no corresponding value found in option of the section from the configuration file.

    """

    def __init__(self, value, option, section, paths):
        self.msg = "No value: '{0}'".format(value)
        self.msg += "\n<option: '{0}'>".format(option)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class InvalidNetCDFFile(Exception):
    """
    Raised when not a NetCDF file.

    """

    def __init__(self, path):
        self.msg = "Invalid or unknown file format. Only support NetCDF file."
        self.msg += "\n<file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path, variable=None):
        if variable:
            self.msg = "No attribute: '{0}'".format(attribute)
            self.msg += "\n<variable: '{0}'>".format(variable)
        else:
            self.msg = "No global attribute: '{0}'".format(attribute)
        self.msg += "\n<file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "No variable: '{0}'".format(variable)
        self.msg += "\n<file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)
