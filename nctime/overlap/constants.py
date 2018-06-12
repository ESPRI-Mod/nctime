#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this module.

"""

# List of variable required by each process
PROCESS_VARS = ['pattern',
                'ref_calendar',
                'progress',
                'nbfiles',
                'lock']

# CMIP6 filename format
CMIP6_FILENAME_PATTERN = '^(?P<variable_id>[\w.-]+)_' \
                         '(?P<table_id>[\w.-]+)_' \
                         '(?P<source_id>[\w.-]+)_' \
                         '(?P<experiment_id>[\w.-]+)_' \
                         '(?P<variant_label>[\w.-]+)_' \
                         '(?P<grid_label>[^-_]+)' \
                         '(_(?P<period_start>[\w.-]+)-(?P<period_end>[\w.-]+))?' \
                         '\\.nc$'

# Facet to ignore
IGNORED_FACETS = ['period_start', 'period_end']
