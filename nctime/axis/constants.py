#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# Database connexion timeout (in sec)
TIMEOUT = 120

# Errors that return exit code = 1
EXIT_ERRORS = ['005', '999']

# Status messages
STATUS = {'000': 'Time axis seems OK',
          '001': 'Incorrect time axis over one or several time steps',
          '002': 'Time units must be unchanged for the same dataset',
          '003': 'Last timestamp differs from end timestamp of filename',
          '004': 'An instantaneous time axis should not embed time boundaries',
          '005': 'An averaged time axis should embed time boundaries',
          '006': 'Incorrect time bounds over one or several time steps',
          '007': 'Calendar must be unchanged for the same dataset',
          '008': 'Last date differs from end date of filename',
          '999': 'Other error'}
