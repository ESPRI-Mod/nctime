#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""
from netcdftime import datetime

# Program version
VERSION = '3.4.0'

# Date
VERSION_DATE = datetime(year=2017, month=10, day=19).strftime("%Y-%d-%m")

# Help
PROGRAM_DESC = \
    """
    NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely
    used following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and
    time are included in NetCDF files as vectors.|n|n
    
    The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate
    models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse,
    produced erroneous results, due to problems in the time axis description.|n|n
    
    Moreover, to produce smaller files, the NetCDF files are splitted over the time period. Consequently, the
    different MIP archives designs include the period dates into the filename. The scheme of chunked files in MIP
    projects is not fixed and depends on several parameters (the institute, the model, the frequency, etc.). These
    different schemes lead to unnecessary overlapping files with a more complex folder reading and wasting disk
    space.|n|n
    
    "nctime" is a Python toolbox allowing you to easily:|n
    i. Highlight chunked NetCDF files producing overlaps in a time series and delete all chunked overlapping
    files,|n
    ii. Check and rebuild a MIP-compliant time axis of your NetCDF files.|n|n
    
    Note that "nctime" is based on uncorrupted filename period dates and properly-defined times units, time
    calendar and frequency NetCDF attributes.|n|n
    
    See full documentation and references on http://prodiguer.github.io/nctime/.

    """

EPILOG = \
    """
    Developed by:|n
    Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)

    """

OPTIONAL = \
    """
    Optional arguments
    
    """

POSITIONAL = \
    """
    Positional arguments
    
    """

HELP = \
    """
    Show this help message and exit.

    """

VERSION_HELP = \
    """
    Program version.

    """

SUBCOMMANDS = \
    """
    Subcommands
    
    """

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
    Logfile directory. <log_dir> is read from configuration |n
    file if not submitted. If no <log_dir>, current working |n
    directory is used instead. An existing logfile can be submitted.|n
    If not, standard output is used.

    """

VERBOSE_HELP = \
    """
    Verbose mode.

    """

DIRECTORY_HELP = \
    """
    One or more variable directories to diagnose.|n
    Unix wildcards are allowed.
    
    """

OVERLAP_DESC = \
    """
    To produce smaller files, the NetCDF files are splited over the time period. Consequently, the different MIP
    archives designs include the period dates into the filename.|n|n
    
    The scheme of chunked files in MIP projects is not fixed and depends on several parameters (the institute,
    the model, the frequency, etc.). These different schemes lead to unnecessary overlapping files with a more
    complex folder reading and wasting disk space.|n|n
    
    "overlap" is a command-line tool allowing you to easily highlight chunked NetCDF files producing overlaps in
    a time series and delete all chunked overlapping files in your MIP variable directories in order to save
    disk space.|n|n
    
    Note that:|n
    i. Only complete overlaps are detected. For example, if a file goes from 1991 to 2010 and
    another goes from 2001 to 2020, the overlap is partial. If the second file goes from 2001 to 2010 so the
    overlap is complete and the second file can be removed without loss of information.|n
    ii. "overlap" is based on uncorrupted filename period dates and properly-defined times units, time calendar
    and frequency NetCDF attributes.|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

OVERLAP_HELP = \
    """
    Highlight chunked NetCDF files producing overlap in a time series.|n
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
    NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely
    used following the CF conventions. Dimensions such as longitude, latitude and time are included in NetCDF
    files as vectors.|n|n
    
    The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled
    climate models and leads to flawed studies or unused data.|n|n
    
    "nctime axis" is a command-line tool allowing you to easily check and rebuild a MIP-compliant time axis of
    your downloaded files from the ESGF.|n|n
    
    Note that:|n
    (i) "nctime axis" is based on uncorrupted filename period dates and properly-defined times units, time
    calendar and frequency NetCDF attributes.|n
    (ii) To rebuild a proper time axis, the dates from filename are expected to set the first time boundary and
    not the middle of the time interval. This is always the case for the instantaneous axis or frequencies
    greater than the daily frequency. Consequently, the 3-6 hourly files with an averaged time axis requires a
    date time correction.|n|n
    
    Time axis status returned:|n
    000: Unmodified time axis,|n
    001: Corrected time axis because wrong time steps,|n
    002: Corrected time axis because of changing time units,|n
    003: Ignored time axis because of inconsistency between last date of time axis and end date of filename
    period (e.g., wrong time axis length),|n
    004: Corrected time axis deleting time boundaries for instant time,|n
    005: Ignored averaged time axis without time boundaries,|n
    006: Corrected time bounds because wrong time steps.|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

AXIS_HELP = \
    """
    Rewrite and/or check time axis of MIP NetCDF files.|n
    See "nctime axis -h" for full help.
    
    """

WRITE_HELP = \
    """
    Rewrites time axis depending on checking.|n
    THIS ACTION DEFINITELY MODIFY INPUT FILES!
    
    """

FORCE_HELP = \
    """
    Forces time axis writing overpassing checking step.|n
    THIS ACTION DEFINITELY MODIFY INPUT FILES!
    
    """

DB_HELP = \
    """
    SQLite database path to persist diagnostics. <db_path> is |n
    read from configuration file if not submitted. If no <db_path>, |n
    current working directory is used instead. If not, time |n
    diagnostic is not saved.

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

# Default time units
DEFAULT_TIME_UNITS = {'cordex':        'days since 1949-12-01 00:00:00',
                      'cordex-adjust': 'days since 1949-12-01 00:00:00'}

# Required NetCDF global attributes
REQUIRED_ATTRIBUTES = ['project_id', 'model_id', 'frequency']

# Required NetCDF time attributes
REQUIRED_TIME_ATTRIBUTES = ['units', 'calendar']

# Required options
REQUIRED_OPTIONS = ['checksum_type', 'filename_format']


