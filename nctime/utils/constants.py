#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""
from netcdftime import datetime

# Program version
VERSION = '4.4.8'

# Date
VERSION_DATE = datetime(year=2018, month=7, day=13).strftime("%Y-%d-%m")

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

# Help
TITLE = \
    """
    _________________________|n
    .___ ___| |_ _ _____ ___.|n
    | | | __| __| | . . | -_||n
    |_|_|___|_| |_|_|_|_|___||n
    
    """
URL = \
    """
    See full documentation and references at:|n
    http://prodiguer.github.io/nctime/.

    """

DEFAULT = \
    """
    The default values are displayed next to the corresponding flags.

    """

PROGRAM_DESC = \
    """
    {}|n|n
                         
    NetCDF files describe all required dimensions to work with. Dimensions such as longitude, latitude and time are
    included in NetCDF files as vectors. Time is a key dimension that could lead to flawed studies or unused data
    if misdeclared. "nctime" allows to easily diagnose the time definition of NetCDF files to ensure a proper
    analysis:|n|n
    
    i. Check time series continuity (i.e., highlight missing/overlapping files),|n|n

    ii. Check time axis squareness (i.e., rebuilt a convention-compliant time axis).|n|n
    
    {}|n|n
    
    {}
   
    """.format(TITLE, URL, DEFAULT)

EPILOG = \
    """
    Developed by:|n
    Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)|n
    Laliberte, F. (ExArch - frederic.laliberte@utoronto.ca)

    """

OPTIONAL = \
    """Optional arguments"""

POSITIONAL = \
    """Positional arguments"""

HELP = \
    """
    Show this help message and exit.

    """

VERSION_HELP = \
    """
    Program version.
    
    """

SUBCOMMANDS = \
    """Subcommands"""

PROJECT_HELP = \
    """
    Project name corresponding to a section of the|n
    configuration file. If not submitted project id|n
    is deduced from first netCDF file scanned.
    
    """

INI_HELP = \
    """
    Initialization/configuration directory containing|n
    "esg.<project>.ini" files. If not specified, the|n
    environment variable ESGINI is used. If not exist|n
    usual datanode directory is used.

    """

LOG_HELP = \
    """
    Logfile directory.|n
    If submitted without value, the default directory|n
    is: $PWD/logs.
    If not, standard output is used.

    """

VERBOSE_HELP = \
    """
    Verbose mode.

    """

ALL_HELP = \
    """
    Display all results.
    Default only shows error(s).

    """
DIRECTORY_HELP = \
    """
    One or more variable directories to diagnose.|n
    Unix wildcards are allowed.
    
    """

OVERLAP_DESC = \
    """
    {}|n|n
    
    The scheme of chunked files in archive designs is not fixed and depends on several parameters (the
    institute, the model, the frequency, etc.). These different schemes lead to unnecessary overlapping files
    with a more complex folder reading, wasting disk space or broken time series. "nctime overlap" allows to
    easily analyse and correct the time series continuity (i.e., broken time series, overlapping files).|n|n
    
    {}|n|n
    
    {}
    
    """.format(TITLE, URL, DEFAULT)

OVERLAP_HELP = \
    """
    Checks time series continuity.|n
    See "nctime overlap -h" for full help.
    
    """

RESOLVE_HELP = \
    """
    Resolves overlapping files.|n
    THIS ACTION DEFINITELY MODIFY INPUT DIRECTORY!

    """

FULL_ONLY_HELP = \
    """
    Removes only full overlapping files.|n
    THIS ACTION DEFINITELY MODIFY INPUT DIRECTORY!
    
    """

AXIS_DESC = \
    """
    {}|n|n
    
    The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate
    models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse,
    produced erroneous results, due to problems in the time axis description. "nctime axis" allows to easily
    check and rebuild a convention-compliant time axis for NetCDF files.|n|n

    {}|n|n
    
    {}
    
    """.format(TITLE, URL, DEFAULT)

AXIS_HELP = \
    """
    Checks time axis squareness.|n
    See "nctime axis -h" for full help.
    
    """

ON_FLY_HELP = \
    """
    Ignore the test on end date consistency for on going|n
    simulation (this also include completed files).

    """

CARD_HELP = \
    """
    The libIGCM directory with "run.card" and "config.card"|n
    of the simulation. This option is IPSL-specific.

    """

START_HELP = \
    """
    Theoretical starting timestamp to consider.|n
    Default is to consider timestamps from filename.

    """

END_HELP = \
    """
    Theoretical ending timestamp to consider.|n
    Default is to consider timestamps from filename.

    """

LIMIT_HELP = \
    """
    Limit of displayed wrong timesteps (if exist)|n
    Default is set to 5. If submitted without value, all|n
    timesteps are printed. 

    """

IGNORE_ERROR_HELP = \
    """
    One or several error codes to ignore comma-separated.

    """

WRITE_HELP = \
    """
    Rewrites time axis depending on checking.|n
    THIS ACTION DEFINITELY MODIFY INPUT FILES!
    
    """

FORCE_HELP = \
    """
    Forces time axis rewriting.|n
    THIS ACTION DEFINITELY MODIFY INPUT FILES!
    
    """

MAX_PROCESSES_HELP = \
    """
    Number of maximal processes to simultaneously treat|n
    several files. Max is the CPU count.|n
    Set to 1 seems sequential processing.|n
    Set to -1 uses the max CPU count.|n
    Default is set to 4 processes.
    
    """

IGNORE_DIR_HELP = \
    """
    Filter directories NON-matching the regular expression.|n
    Default ignore paths with folder name(s) starting with|n
    "." pattern. (Regular expression must match from start|n
    of path; prefix with ".*" if required.)

    """

INCLUDE_FILE_HELP = \
    """
    Filter files matching the regular expression.|n
    Duplicate the flag to set several filters.|n
    Default only include NetCDF files.

    """

EXCLUDE_FILE_HELP = \
    """
    Filter files NON-matching the regular expression.|n
    Duplicate the flag to set several filters.|n
    Default only exclude hidden files (with names not|n
    starting with "."). It excludes fixed data without|n
    time axis in any case.

    """

SET_INC_HELP = \
    """
    Overwrites the default time increment of a |n
    table:frequency couple. Duplicate the flag to |n
    overwrites several increments. "all" keyword is allowed|n
    to overwrite increment for all frequencies or all tables|n
    (e.g., all:mon=2M will set monthly frequency equivalent to |n
    2 Months between time steps instead of 1 for all tables).|n
    Available units are: s, m, h, D, M, Y respectively for|n
    seconds, minutes, hours, days, months, years.

    """

CALENDAR_HELP = \
    """
    Defines reference calendar for the check.|n
    Default is to consider the calendar from|n 
    the first file scanned.|n
    Available calendars are those from CF conventions:|n
    gregorian, standard, proleptic_gregorian, noleap,|n
    365_day, all_leap, 366_day, 360_day.
    
    """

UNITS_HELP = \
    """
    Defines reference time units for the check.|n
    Default is to consider the time units from|n 
    the first file scanned.|n
    Available time units format is:|n
    "<units> since YYYY-MM-DD HH:mm:ss" where|n
    <units> stands for seconds, minutes, hours|n
    or days.
    
    """

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
AVERAGE_CORRECTION_FREQ = ['day', 'mon', 'monPt', 'yr', 'yrPt']

# Frequencies to consider in case of non-instant time correction
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