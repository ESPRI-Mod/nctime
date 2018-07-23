#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Status messages
STATUS = {'000': 'Time axis seems OK',
          '001': 'Incorrect time axis over one or several time steps',
          '002': 'Time units must be unchanged for the same dataset',
          '003': 'Last date is earlier than end date from filename',
          '004': 'An instantaneous time axis should not embed time boundaries',
          '005': 'An averaged time axis should embed time boundaries',
          '006': 'Incorrect time bounds over one or several time steps',
          '007': 'Calendar must be unchanged for the same dataset',
          '008': 'Last date is later than end date of filename',
          '999': 'Other error'}

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
