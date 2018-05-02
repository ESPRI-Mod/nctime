#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""
from netcdftime import datetime

# Program version
VERSION = '4.1.0'

# Date
VERSION_DATE = datetime(year=2018, month=5, day=2).strftime("%Y-%d-%m")

# Help
PROGRAM_DESC = \
    """
    NetCDF files describe all required dimensions to work with. Dimensions such as longitude, latitude and time are
    included in NetCDF files as vectors. Time is a key dimension that could lead to flawed studies or unused data
    if misdeclared. "nctime" allows to easily diagnose the time definition of NetCDF files to ensure a proper
    analysis:|n|n
    
    i. Check time series continuity (i.e., highlight missing/overlapping files),|n|n

    ii. Check time axis squareness (i.e., rebuilt a convention-compliant time axis).|n|n
    
    See full documentation and references on http://prodiguer.github.io/nctime/.

    """

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
    Required project name corresponding to a section of the|n
    configuration file.
    
    """

INI_HELP = \
    """
    Initialization/configuration directory containing|n
    "esg.ini" and "esg.<project>.ini" files.|n
    If not specified, the usual datanode directory|n
    is used.

    """

LOG_HELP = \
    """
    Logfile directory.|n
    If not, standard output is used.

    """

VERBOSE_HELP = \
    """
    Verbose mode.

    """

ERRORS_ONLY_HELP = \
    """
    Shows error(s) only: overlaps and broken|n
    time periods.

    """
DIRECTORY_HELP = \
    """
    One or more variable directories to diagnose.|n
    Unix wildcards are allowed.
    
    """

OVERLAP_DESC = \
    """
    The scheme of chunked files in archive designs is not fixed and depends on several parameters (the
    institute, the model, the frequency, etc.). These different schemes lead to unnecessary overlapping files
    with a more complex folder reading, wasting disk space or broken time series. "nctime overlap" allows to
    easily analyse and correct the time series continuity (i.e., broken time series, overlapping files).|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

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

FULL_OVERLAP_ONLY_HELP = \
    """
    Removes only full overlapping files.|n
    THIS ACTION DEFINITELY MODIFY INPUT DIRECTORY!
    
    """

AXIS_DESC = \
    """
    The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate
    models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse,
    produced erroneous results, due to problems in the time axis description. "nctime axis" allows to easily
    check and rebuild a convention-compliant time axis for NetCDF files.|n|n

    The default values are displayed next to the corresponding flags.
    
    """

AXIS_HELP = \
    """
    Checks time axis squareness.|n
    See "nctime axis -h" for full help.
    
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

DB_HELP = \
    """
    Persists diagnostics into SQLite database.|n
    If not, time diagnostic is not saved.

    """

MAX_THREADS_HELP = \
    """
    Number of maximal threads to simultaneously process|n
    several files (useful if checksum calculation is|n
    enabled). Set to one seems sequential processing.
    
    """

# Half-hour numerical definition
HALF_HOUR = 0.125 / 6.0

# Filename date correction for 3hr and 6hr files
TIME_CORRECTION = {'3hr': {'period_start': {'000000': 0.0,
                                            '003000': -HALF_HOUR,
                                            '013000': -HALF_HOUR * 3,
                                            '030000': -HALF_HOUR * 6},
                           'period_end': {'210000': 0.0,
                                          '213000': -HALF_HOUR,
                                          '223000': -HALF_HOUR * 3,
                                          '230000': -HALF_HOUR * 4,
                                          '000000': -HALF_HOUR * 6,
                                          '003000': -HALF_HOUR * 7}},
                   '6hr': {'period_start': {'000000': 0.0,
                                            '060000': -HALF_HOUR * 12},
                           'period_end': {'180000': 0.0,
                                          '230000': -HALF_HOUR * 10,
                                          '000000': -HALF_HOUR * 12}}}

# Default time units
DEFAULT_TIME_UNITS = {'cordex': 'days since 1949-12-01 00:00:00',
                      'cordex-adjust': 'days since 1949-12-01 00:00:00'}
