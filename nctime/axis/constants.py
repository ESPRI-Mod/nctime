#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Status keys
ERROR_TIME_AXIS_OK = '000'
ERROR_TIME_AXIS_KO = '001'
ERROR_TIME_BOUNDS_INS = '002'
ERROR_TIME_BOUNDS_AVE = '003'
ERROR_TIME_BOUNDS_KO = '004'
ERROR_TIME_UNITS = '005'
ERROR_TIME_CALENDAR = '006'
ERROR_END_DATE_IN_VS_NAME = '007a'
ERROR_END_DATE_NAME_VS_IN = '007b'
ERROR_END_DATE_NAME_VS_REF = '008a'
ERROR_END_DATE_REF_VS_NAME = '008b'
ERROR_END_DATE_IN_VS_REF = '009a'
ERROR_END_DATE_REF_VS_IN = '009b'
ERROR_START_DATE_IN_VS_NAME = '010a'
ERROR_START_DATE_NAME_VS_IN = '010b'

ERROR_CORRECTED_SET = (ERROR_TIME_AXIS_KO,
                       ERROR_TIME_BOUNDS_INS,
                       ERROR_TIME_BOUNDS_KO,
                       ERROR_TIME_UNITS,
                       ERROR_TIME_CALENDAR,
                       ERROR_END_DATE_IN_VS_NAME,
                       ERROR_END_DATE_NAME_VS_IN,
                       ERROR_END_DATE_REF_VS_IN,
                       ERROR_END_DATE_IN_VS_REF,
                       ERROR_END_DATE_REF_VS_NAME,
                       ERROR_END_DATE_NAME_VS_REF)

# Status messages
STATUS = {ERROR_TIME_AXIS_OK: 'Time axis seems OK',
          ERROR_TIME_AXIS_KO: 'Incorrect time axis over one or several time steps',
          ERROR_TIME_BOUNDS_INS: 'An instantaneous time axis should not embed time boundaries',
          ERROR_TIME_BOUNDS_AVE: 'An averaged time axis should embed time boundaries',
          ERROR_TIME_BOUNDS_KO: 'Incorrect time bounds over one or several time steps',
          ERROR_TIME_UNITS: 'Time units must be unchanged for the same dataset',
          ERROR_TIME_CALENDAR: 'Calendar must be unchanged for the same dataset',
          ERROR_END_DATE_IN_VS_NAME: 'End date in file is earlier than end date from filename',
          ERROR_END_DATE_NAME_VS_IN: 'End date in file is late than end date from filename',
          ERROR_END_DATE_NAME_VS_REF: 'End date from filename is earlier than theoretical end date',
          ERROR_END_DATE_REF_VS_NAME: 'End date from filename is later than theoretical end date',
          ERROR_END_DATE_IN_VS_REF: 'End date in file is earlier than theoretical end date',
          ERROR_END_DATE_REF_VS_IN: 'End date in file is later than theoretical end date',
          ERROR_START_DATE_IN_VS_NAME: 'Start date in file is earlier than start date from filename',
          ERROR_START_DATE_NAME_VS_IN: 'Start date in file is later than start date from filename'}

# List of variable required by each process
PROCESS_VARS = ['pattern',
                'ref_units',
                'ref_calendar',
                'ref_start',
                'ref_end',
                'write',
                'force',
                'on_fly',
                'limit',
                'lock',
                'progress',
                'nbfiles',
                'ignore_codes']

# Number of decimal to keep in axis truncation
NDECIMALS = 8
