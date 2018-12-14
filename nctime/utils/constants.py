#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""
from datetime import datetime as dt

# Program version
VERSION = '4.6.3'

# Date
VERSION_DATE = dt(year=2018, month=12, day=14).strftime("%Y-%d-%m")

# Cards name
RUN_CARD = 'run.card'
CONF_CARD = 'config.card'

# Filedef directory format
FILEDEF_ROOT = '/ccc/work/cont003/igcmg/igcmg/IGCM'
FILEDEF_DIRECTORY_FORMAT = '{root}/CMIP6/{longname}/{modelname}/{experimentname}/{member}/{year}'

# Shell colors map
SHELL_COLORS = {'red': 1,
                'green': 2,
                'yellow': 3,
                'blue': 4,
                'magenta': 5,
                'cyan': 6,
                'gray': 7}

# Default time units
DEFAULT_TIME_UNITS = {'cordex': 'days since 1949-12-01 00:00:00',
                      'cordex-adjust': 'days since 1949-12-01 00:00:00'}

# Climatology file suffix
CLIM_SUFFIX = '-clim.nc'

# Frequency increment
FREQ_INC = {('None', 'subhr'): [30, 'minutes'],
            ('None', 'subhrPt'): [30, 'minutes'],
            ('None', '1hr'): [1, 'hours'],
            ('None', '1hrCM'): [1, 'hours'],
            ('None', '1hrPt'): [1, 'hours'],
            ('None', '3hr'): [3, 'hours'],
            ('None', '3hrPt'): [3, 'hours'],
            ('None', '6hr'): [6, 'hours'],
            ('None', '6hrPt'): [6, 'hours'],
            ('None', 'day'): [1, 'days'],
            ('None', 'dec'): [10, 'years'],
            ('None', 'mon'): [1, 'months'],
            ('None', 'monC'): [1, 'months'],
            ('None', 'monPt'): [1, 'months'],
            ('None', 'yr'): [1, 'years'],
            ('None', 'yrPt'): [1, 'years'],
            ('3hr', '3hr'): [3, 'hours'],
            ('3hr', '3hrPt'): [3, 'hours'],
            ('3hrCurt', '3hr'): [3, 'hours'],
            ('3hrMlev', '3hr'): [3, 'hours'],
            ('3hrPlev', '3hr'): [3, 'hours'],
            ('3hrSlev', '3hr'): [3, 'hours'],
            ('6hrLev', '6hrPt'): [6, 'hours'],
            ('6hrLev', '6hr'): [6, 'hours'],
            ('6hrPlev', '6hr'): [6, 'hours'],
            ('6hrPlevPt', '6hr'): [6, 'hours'],
            ('6hrPlevPt', '6hrPt'): [6, 'hours'],
            ('Aclim', 'monClim'): [1, 'months'],
            ('AERday', 'day'): [1, 'days'],
            ('AERhr', '1hr'): [1, 'hours'],
            ('AERmon', 'mon'): [1, 'months'],
            ('AERmonZ', 'mon'): [1, 'months'],
            ('aero', 'mon'): [1, 'months'],
            ('Amon', 'mon'): [1, 'months'],
            ('Amon', 'monC'): [1, 'months'],
            ('Amon', 'monClim'): [1, 'months'],
            ('AmonExtras', 'mon'): [1, 'months'],
            ('CF3hr', '3hrPt'): [3, 'hours'],
            ('cf3hr', '3hr'): [3, 'hours'],
            ('CFday', 'day'): [1, 'days'],
            ('cfDay', 'day'): [1, 'days'],
            ('CFmon', 'mon'): [1, 'months'],
            ('cfMon', 'mon'): [1, 'months'],
            ('cfOff', 'mon'): [1, 'months'],
            ('cfSites', '3hr'): [3, 'hours'],
            ('cfSites', '6hr'): [6, 'hours'],
            ('cfSites', 'subhr'): [30, 'minutes'],
            ('CFsubhr', 'subhrPt'): [30, 'minutes'],
            ('day', 'day'): [1, 'days'],
            ('dayExtras', 'day'): [1, 'days'],
            ('E1hr', '1hr'): [1, 'hours'],
            ('E1hr', '1hrPt'): [1, 'hours'],
            ('E1hrClimMon', '1hrCM'): [1, 'hours'],
            ('E3hr', '3hr'): [3, 'hours'],
            ('E3hrPt', '3hrPt'): [3, 'hours'],
            ('E6hrZ', '6hr'): [6, 'hours'],
            ('E6hrZ', '6hrPt'): [6, 'hours'],
            ('Eday', 'day'): [1, 'days'],
            ('EdayZ', 'day'): [1, 'days'],
            ('Emon', 'mon'): [1, 'months'],
            ('EmonZ', 'mon'): [1, 'months'],
            ('Esubhr', 'subhrPt'): [30, 'minutes'],
            ('Eyr', 'yr'): [1, 'years'],
            ('Eyr', 'yrPt'): [1, 'years'],
            ('ImonAnt', 'mon'): [1, 'months'],
            ('ImonGre', 'mon'): [1, 'months'],
            ('IyrAnt', 'yr'): [1, 'years'],
            ('IyrGre', 'yr'): [1, 'years'],
            ('Lclim', 'monClim'): [1, 'months'],
            ('LIclim', 'monClim'): [1, 'months'],
            ('LImon', 'mon'): [1, 'months'],
            ('Lmon', 'mon'): [1, 'months'],
            ('Oclim', 'monClim'): [1, 'months'],
            ('Oclim', 'monC'): [1, 'months'],
            ('Oday', 'day'): [1, 'days'],
            ('Odec', 'dec'): [10, 'years'],
            ('OIclim', 'monClim'): [1, 'months'],
            ('OImon', 'mon'): [1, 'months'],
            ('Omon', 'mon'): [1, 'months'],
            ('OmonExtras', 'mon'): [1, 'months'],
            ('Oyr', 'yr'): [1, 'years'],
            ('OyrExtras', 'yr'): [1, 'years'],
            ('SIday', 'day'): [1, 'days'],
            ('SImon', 'mon'): [1, 'months'],
            ('SImon', 'monPt'): [1, 'months'],
            ('sites', 'subhr'): [30, 'minutes'],
            ('HOMAL3hrPt', '3hrPt'): [3, 'hours'],
            ('HOMAL3hrPt', '3hr'): [3, 'hours'],
            ('HOMALmon', 'mon'): [1, 'months'],
            ('HOMEPmon', 'mon'): [1, 'months'],
            ('HOMOImon', 'mon'): [1, 'months']}

# Known time units
TIME_UNITS = {'s': 'seconds',
              'm': 'minutes',
              'h': 'hours',
              'D': 'days',
              'M': 'months',
              'Y': 'years'}

# Frequencies to consider in case of non-instant time correction
AVERAGE_CORRECTION_FREQ = ['day', 'mon', 'monPt', 'yr', 'yrPt', '1hrCM']

# Climatology frequencies
CLIMATOLOGY_FREQ = ['monC', 'monClim', '1hrCM']

# Available CF calendars
CALENDARS = ['gregorian',
             'standard',
             'proleptic_gregorian',
             'noleap',
             'julian',
             '365_day',
             'all_leap',
             '366_day',
             '360_day']

TIME_UNITS_FORMAT = "{seconds,minutes,hours,days} since YYYY-MM-DD [HH:mm:ss]"
