#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""
from netcdftime import datetime

# Program version
VERSION = '3.9.9'

# Date
VERSION_DATE = datetime(year=2017, month=10, day=18).strftime("%Y-%d-%m")

# Filename date correction for 3hr and 6hr files
HALF_HOUR = 0.125 / 6.0
TIME_CORRECTION = {'3hr': {'start_period': {'000000': 0.0,
                                            '003000': -HALF_HOUR,
                                            '013000': -HALF_HOUR * 3,
                                            '030000': -HALF_HOUR * 6},
                           'end_period':   {'210000': 0.0,
                                            '213000': -HALF_HOUR,
                                            '223000': -HALF_HOUR * 3,
                                            '230000': -HALF_HOUR * 4,
                                            '000000': -HALF_HOUR * 6,
                                            '003000': -HALF_HOUR * 7}},
                   '6hr': {'start_period': {'000000': 0.0,
                                            '060000': -HALF_HOUR * 12},
                           'end_period':   {'180000': 0.0,
                                            '230000': -HALF_HOUR * 10,
                                            '000000': -HALF_HOUR * 12}}}

# Required NetCDF global attributes
REQUIRED_ATTRIBUTES = ['project_id', 'model_id', 'frequency']

# Required NetCDF time attributes
REQUIRED_TIME_ATTRIBUTES = ['units', 'calendar']

# Required options
REQUIRED_OPTIONS = ['checksum_type', 'filename_format']
