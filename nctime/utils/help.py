#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used for help message.

"""

from custom_print import *

# Help
TITLE = COLOR('yellow').bold("""_________________________
.___ ___| |_ _ _____ ___.
| | | __| __| | . . | -_|
|_|_|___|_| |_|_|_|_|___|""")

INTRO = """netCDF files describe all required dimensions to work with. Dimensions such as longitude, latitude and time are included in netCDF files as vectors. Time is a key dimension that could lead to flawed studies or unused data if misdeclared. "nctime" allows to easily diagnose the time definition of netCDF files to ensure a proper analysis."""

URL = COLOR('gray').italic("""See full documentation and references at http://prodiguer.github.io/nctime/""")

DEFAULT = COLOR('white').italic("""The default values are displayed next to the corresponding flags.""")

PROGRAM_DESC = {
    'axis': """
{}

{} The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the time axis description. The netCDF Time Axis Checker ("nctxck") allows to easily check the time axis correctness by rebuilding a convention-compliant time axis for NetCDF files.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'overlap': """
{}

{}  The scheme of chunked files in archive designs is not fixed and depends on several parameters (the institute, the model, the frequency, etc.). These different schemes lead to unnecessary overlapping files with a more complex folder reading, wasting disk space or broken time series. The netCDF Time Coverage Checker (nctcck) allows to easily analyse and correct the time series continuity (i.e., broken time series, overlapping files). 

{}

{}""".format(TITLE, INTRO, URL, DEFAULT)}

EPILOG = COLOR('gray').italic("""Developed by:
    Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)
    Laliberte, F.   (ExArch - frederic.laliberte@utoronto.ca)""")

OPTIONAL = COLOR('blue')("""Optional arguments""")

POSITIONAL = COLOR('magenta')("""Positional arguments""")

HELP = """Show this help message and exit.

"""

VERSION_HELP = """Program version.

"""

PROJECT_HELP = """Project name corresponding to a section of the configuration file.
If not submitted project id is deduced from first netCDF file scanned.

"""

INI_HELP = """Initialization/configuration directory containing "esg.<project>.ini" files.
If not specified, the environment variable ESGINI_DIR is used.
If not exist usual datanode directory is used.

"""

LOG_HELP = """Logfile directory.
If submitted without value, the default directory is: $PWD/logs.
If not, standard output is used.

"""

VERBOSE_HELP = """Verbose mode.

"""

ALL_HELP = """Display all results.
Default only shows error(s).

"""

INPUT_HELP = """One or more variable directories or files to diagnose.
Unix wildcards are allowed.

"""

DIRECTORY_HELP = """One or more variable directories to diagnose.
Unix wildcards are allowed.

"""

RESOLVE_HELP = """Resolves overlapping files.
THIS ACTION DEFINITELY MODIFY INPUT FILES!

"""

FULL_ONLY_HELP = """Removes only full overlapping files.
THIS ACTION DEFINITELY MODIFY INPUT FILES!

"""

ON_FLY_HELP = """Ignore the test on end date consistency for on going simulation (this also include completed files).

"""

XML_HELP = """One or several directory with DR2XML files used for the simulation.

"""

CARD_HELP = """The libIGCM directory with "run.card" and "config.card" of the simulation.
This option is IPSL-specific.

"""

START_HELP = {
    'overlap': """Starting timestamp for the covered period.
Default is the minimum of all timestamps among filenames.

""",
    'axis': """Theoretical starting timestamp to consider.
Default is to consider timestamps from filename.

"""}

END_HELP = {
    'overlap': """Theoretical ending timestamp to consider.
Default is to consider timestamps from filename.

""",
    'axis':
        """Theoretical ending timestamp to consider.
Default is to consider timestamps from filename.

"""}

LIMIT_HELP = """Limit of displayed wrong timesteps (if exist).
Default is set to 5. If submitted without value, all timesteps are printed.

"""

IGNORE_ERROR_HELP = """One or several error codes to ignore comma-separated.

"""

WRITE_HELP = """Rewrites time axis depending on checking.
THIS ACTION DEFINITELY MODIFY INPUT FILES!

"""

FORCE_HELP = """Forces time axis rewriting.
THIS ACTION DEFINITELY MODIFY INPUT FILES!

"""

MAX_PROCESSES_HELP = """Number of maximal processes to simultaneously treat several files. Max is the CPU count.
Set to 1 seems sequential processing.
Set to -1 uses the max CPU count.
Default is set to 4 processes.

"""

IGNORE_DIR_HELP = """Filter directories NON-matching the regular expression.
Default ignore paths with folder name(s) starting with "." pattern.
(Regular expression must match from start of path; prefix with ".*" if required.)

"""

INCLUDE_FILE_HELP = """Filter files matching the regular expression.
Duplicate the flag to set several filters.
Default only include NetCDF files.

    """

EXCLUDE_FILE_HELP = """Filter files NON-matching the regular expression.
Duplicate the flag to set several filters.
Default only exclude hidden files (with names not
starting with "."). It excludes fixed data without
time axis in any case.

"""

SET_INC_HELP = """Overwrites the default time increment of a table:frequency couple.
Duplicate the flag to overwrite several increments.
"all" keyword is allowed to overwrite increment for all frequencies or all tables (e.g., all:mon=2M will set monthly frequency equivalent to 2 Months between time steps instead of 1 for all tables).
Available units are: s, m, h, D, M, Y respectively for seconds, minutes, hours, days, months, years.

"""

CALENDAR_HELP = """Defines reference calendar for the check.
Default is to consider the calendar from the first file scanned.
Available calendars are those from CF conventions:
gregorian, standard, proleptic_gregorian, noleap, 365_day, all_leap, 366_day, 360_day.

"""

UNITS_HELP = """Defines reference time units for the check.
Default is to consider the time units from the first file scanned.
Available time units format is "<units> since YYYY-MM-DD HH:mm:ss" where <units> stands for seconds, minutes, hours or days.

"""

COLOR_HELP = """Enable colors. (Default is to enable when writing to a terminal.)

"""

NO_COLOR_HELP = """Disable colors.

"""
