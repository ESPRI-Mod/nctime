#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

# Module imports
import re
import os
import argparse
import logging
import ConfigParser
import textwrap
from uuid import uuid4
import numpy as np
from argparse import HelpFormatter
from datetime import datetime
from functools import wraps
from netCDF4 import Dataset, date2num, num2date
from multiprocessing.dummy import Pool as ThreadPool
from netcdftime import datetime as phony_datetime
from netcdftime import utime
from textwrap import fill
from glob import glob

# Program version
__version__ = 'v{0} {1}'.format('3.3', datetime(year=2015, month=11, day=30).strftime("%Y-%d-%m"))

# Filaname date correction for 3hr and 6hr files
_HALF_HOUR = 0.125/6.0
_AVERAGED_TIME_CORRECTION = {'3hr': {0: {'000000': 0.0,
                                         '003000': -_HALF_HOUR,
                                         '013000': -_HALF_HOUR*3,
                                         '030000': -_HALF_HOUR*6},
                                     1: {'210000': 0.0,
                                         '213000': -_HALF_HOUR,
                                         '223000': -_HALF_HOUR*3,
                                         '230000': -_HALF_HOUR*4,
                                         '000000': -_HALF_HOUR*6,
                                         '003000': -_HALF_HOUR*7}},
                             '6hr': {0: {'000000': 0.0,
                                         '060000': -_HALF_HOUR*12},
                                     1: {'180000': 0.0,
                                         '230000': -_HALF_HOUR*10,
                                         '000000': -_HALF_HOUR*12}}}

_INSTANT_TIME_CORRECTION = {'3hr': {0: {'000000': _HALF_HOUR*6,
                                        '003000': _HALF_HOUR*5,
                                        '013000': _HALF_HOUR*3,
                                        '030000': 0.0},
                                    1: {'210000': _HALF_HOUR*6,
                                        '213000': _HALF_HOUR*5,
                                        '223000': _HALF_HOUR*3,
                                        '230000': _HALF_HOUR*2,
                                        '000000': 0.0,
                                        '003000': -_HALF_HOUR}},
                            '6hr': {0: {'000000': _HALF_HOUR*12,
                                        '060000': 0.0},
                                    1: {'180000': _HALF_HOUR*12,
                                        '230000': _HALF_HOUR*2,
                                        '000000': 0.0}}}


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +-------------------+-------------+---------------------------------+
    | Attribute         | Type        | Description                     |
    +===================+=============+=================================+
    | *self*.directory  | *str*       | Variable to scan                |
    +-------------------+-------------+---------------------------------+
    | *self*.write      | *boolean*   | True if write mode              |
    +-------------------+-------------+---------------------------------+
    | *self*.force      | *boolean*   | True if force writing           |
    +-------------------+-------------+---------------------------------+
    | *self*.verbose    | *boolean*   | True if verbose mode            |
    +-------------------+-------------+---------------------------------+
    | *self*.project    | *str*       | MIP project                     |
    +-------------------+-------------+---------------------------------+
    | *self*.checksum   | *str*       | The checksum type               |
    +-------------------+-------------+---------------------------------+
    | *self*.cfg        | *callable*  | Configuration file parser       |
    +-------------------+-------------+---------------------------------+
    | *self*.pattern    | *re object* | Filename regex pattern          |
    +-------------------+-------------+---------------------------------+
    | *self*.calendar   | *str*       | NetCDF calendar attribute       |
    +-------------------+-------------+---------------------------------+
    | *self*.frequency  | *str*       | NetCDF frequency attribute      |
    +-------------------+-------------+---------------------------------+
    | *self*.variable   | *str*       | MIP variable                    |
    +-------------------+-------------+---------------------------------+
    | *self*.realm      | *str*       | NetCDF modeling realm attribute |
    +-------------------+-------------+---------------------------------+
    | *self*.tunits     | *str*       | Time units from file            |
    +-------------------+-------------+---------------------------------+
    | *self*.funits     | *str*       | Time units from frequency       |
    +-------------------+-------------+---------------------------------+

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*
    :raises Error: If the project name is inconsistent with the sections names from \
    the configuration file

    """
    def __init__(self, args):
        init_logging(args.log)
        self.directory = check_directory(args.directory)
        self.write = args.write
        self.force = args.force
        self.verbose = args.v
        self.cfg = config_parse(args.i)
        if args.project in self.cfg.sections():
            self.project = args.project
        else:
            raise Exception('No section in configuration file corresponds to "{0}" project. \
                            Supported projects are {1}.'.format(args.project,
                                                                self.cfg.sections()))
        self.pattern = re.compile(self.cfg.get(self.project, 'filename_format'))
        self.frequency = None
        self.instant = None
        self.realm = None
        self.variable = None
        self.checksum = str(self.cfg.defaults()['checksum_type'])
        self.calendar = None
        self.tunits = None
        self.funits = None


class MultilineFormatter(HelpFormatter):
    """
    Curstom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """
    def __init__(self, prog):
        # Overload the HelpFormatter class to increase the help text position
        # and the total text width.
        super(MultilineFormatter, self).__init__(prog, max_help_position=60, width=100)

    def _fill_text(self, text, width, indent):
        # Rewrites the _fill_text method to support multiline description.
        text = self._whitespace_matcher.sub(' ', text).strip()
        multiline_text = ''
        paragraphs = text.split('|n|n ')
        for paragraph in paragraphs:
            lines = paragraph.split('|n ')
            for line in lines:
                formatted_line = textwrap.fill(line, width,
                                               initial_indent=indent,
                                               subsequent_indent=indent) + '\n'
                multiline_text = multiline_text + formatted_line
            multiline_text = multiline_text + '\n'
        return multiline_text

    def _split_lines(self, text, width):
        # Rewrites the _split_lines method to support multiline helps.
        text = self._whitespace_matcher.sub(' ', text).strip()
        lines = text.split('|n ')
        multiline_text = []
        for line in lines:
            multiline_text.append(textwrap.fill(line, width))
        multiline_text[-1] = multiline_text[-1] + '\n'
        return multiline_text


class AxisStatus(object):
    """
    Encapsulates the following file diagnostic to print or save:

    +------------------+-----------+---------------------------------------------------+
    | Attribute        | Type      | Description                                       |
    +==================+===========+===================================================+
    | *self*.directory | *str*     | Variable to scan                                  |
    +------------------+-----------+---------------------------------------------------+
    | *self*.file      | *str*     | Filename                                          |
    +------------------+-----------+---------------------------------------------------+
    | *self*.start     | *str*     | Start date from filename                          |
    +------------------+-----------+---------------------------------------------------+
    | *self*.end       | *str*     | End date from filename                            |
    +------------------+-----------+---------------------------------------------------+
    | *self*.last      | *str*     | Last date from theoretical time axis              |
    +------------------+-----------+---------------------------------------------------+
    | *self*.steps     | *int*     | Time axis length                                  |
    +------------------+-----------+---------------------------------------------------+
    | *self*.instant   | *boolean* | True if instantaneous time axis                   |
    +------------------+-----------+---------------------------------------------------+
    | *self*.calendar  | *str*     | NetCDF calendar attribute                         |
    +------------------+-----------+---------------------------------------------------+
    | *self*.units     | *str*     | Expected time units                               |
    +------------------+-----------+---------------------------------------------------+
    | *self*.control   | *list*    | Errors status                                     |
    +------------------+-----------+---------------------------------------------------+
    | *self*.bnds      | *boolean* | True if time boundaries excpeted and not mistaken |
    +------------------+-----------+---------------------------------------------------+
    | *self*.checksum  | *str*     | New checksum if modified file                     |
    +------------------+-----------+---------------------------------------------------+
    | *self*.axis      | *array*   | Theoretical time axis                             |
    +------------------+-----------+---------------------------------------------------+
    | *self*.time      | *array*   | Time axis from file                               |
    +------------------+-----------+---------------------------------------------------+

    :returns: The axis status
    :rtype: *dict*

    """
    def __init__(self):
        self.directory = None
        self.file = None
        self.start = None
        self.end = None
        self.last = None
        self.steps = None
        self.instant = False
        self.calendar = None
        self.units = None
        self.control = []
        self.bnds = None
        self.checksum = None
        self.axis = None
        self.time = None


def get_args(job):
    """
    Returns parsed command-line arguments. See ``time_axis -h`` for full description.
    A ``job`` dictionnary can be used as developper's entry point to overload the parser.

    :param dict job: Optionnal dictionnary instead of command-line arguments.
    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        description="""NetCDF files describe all dimensions necessary to work with. In the
                    climate community, this format is widely used following the CF conventions.
                    Dimensions such as longitude, latitude and time are included in NetCDF files
                    as vectors.|n|n

                    The time axis is a key dimension. Unfortunately, this time axis often is
                    mistaken in files from coupled climate models and leads to flawed studies
                    or unused data.|n|n

                    "time_axis" is a command-line tool allowing you to easily check and rebuild
                    a MIP-compliant time axis of your downloaded files from the ESGF.|n|n

                    Note that:|n
                    (i) "time_axis" is based on uncorrupted filename period dates and
                    properly-defined times units, time calendar and frequency NetCDF attributes.|n
                    (ii) To rebuild a proper time axis, the dates from filename are expected to
                    set the first time boundary and not the middle of the time interval.
                    This is always the case for the instantaneous axis or frequencies greater
                    than the daily frequency. Consequently, the 3-6 hourly files with an
                    averaged time axis requires a date time correction.|n|n

                    Time axis status returned:|n
                    000: Unmodified time axis,|n
                    001: Corrected time axis because wrong timesteps,|n
                    002: Corrected time axis because of changing time units,|n
                    003: Ignored time axis because of inconsistency between last date of time axis
                     and end date of filename period (e.g., wrong time axis length),|n
                    004: Corrected time axis deleting time boundaries for instant time,|n
                    005: Ignored averaged time axis without time boundaries.|n|n

                    See full documentation on http://cmip5-time-axis.readthedocs.org/|n|n

                    The default values are displayed next to the corresponding flags.""",
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""Developped by:|n
               Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)|n
               Laliberte, F. (ExArch - frederic.laliberte@utoronto.ca)""")
    parser.add_argument(
        'directory',
        nargs='?',
        help="""Variable path to diagnose."""),
    parser.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required project name corresponding to a section of the|n
                configuration file.""")
    parser.add_argument(
        '-i',
        metavar='$PYTHONUSERSITE/timeaxis/config.ini',
        type=str,
        default='{0}/config.ini'.format(os.path.dirname(os.path.abspath(__file__))),
        help="""Path of configuration INI file.""")
    parser.add_argument(
        '--write',
        action='store_true',
        default=False,
        help="""Rewrites time axis depending on checking.|n
                THIS ACTION DEFINITELY MODIFY INPUT FILES!""")
    parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help="""Forces time axis writing overpassing checking step.|n
                THIS ACTION DEFINITELY MODIFY INPUT FILES!""")
    parser.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        nargs='?',
        const=os.getcwd(),
        help="""Logfile directory. If not, standard output is used.""")
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="""Show this help message and exit.""")
    parser.add_argument(
        '-v',
        action='store_true',
        default=False,
        help='Verbose mode.')
    parser.add_argument(
        '-V',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    if job is None:
        return parser.parse_args()
    else:
        return parser.parse_args([job['args']['variable_path'],
                                 '--project', job['args']['project'],
                                 '-i', '/prodigfs/esg/ArchiveTools/sdp/conf/timeaxis.ini',
                                 '--write',
                                 '--logdir', 'synda_logger',
                                 '-v'])


def init_logging(logdir):
    """
    Initiates the logging configuration (output, message formatting).
    In the case of a logfile, the logfile name is unique and formatted as follows:
    `name-YYYYMMDD-HHMMSS-JOBID.log``

    :param str logdir: The relative or absolute logfile directory. If ``None`` the standard \
    output is used.

    """
    if logdir is 'synda_logger':
        # Logger initiates by SYNDA worker
        pass
    elif logdir:
        name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
        logfile = '{0}-{1}-{2}.log'.format(name,
                                           datetime.now().strftime("%Y%m%d-%H%M%S"),
                                           os.getpid())
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
        logging.basicConfig(filename=os.path.join(logdir, logfile),
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(message)s')


def check_directory(path):
    """
    Checks if the supplied directory exists. The path is normalized before without trailing slash.

    :param list paths: The path to check
    :returns: The same path if exists
    :rtype: *str*
    :raises Error: If the directory does not exist

    """
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise Exception('No such directory: {0}'.format(directory))
    return directory


def config_parse(config_path):
    """
    Parses the configuration file if exists.

    :param str config_path: The absolute or relative path of the configuration file
    :returns: The configuration file parser
    :rtype: *dict*
    :raises Error: If no configuration file exists
    :raises Error: If the configuration file parsing fails

    """
    if not os.path.isfile(config_path):
        raise Exception('Configuration file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_path)
    if not cfg:
        raise Exception('Configuration file parsing failed')
    return cfg


def time_init(ctx):
    """
    Returns the required referenced time properties from first file into processing context:
     * The calendar, the frequency and the realm are read from NetCDF global attributes and
     use to detect instantaneous time axis,
     * The NetCDF time units attribute has to be unchanged in respect with CF convention and
     archives designs.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If NetCDF time units attribute is missing
    :raises Error: If NetCDF frequency attribute is missing
    :raises Error: If NetCDF realm attribute is missing
    :raises Error: If NetCDF calendar attribute is missing

    """
    filename = yield_inputs(ctx).next()[0]
    data = Dataset('{0}/{1}'.format(ctx.directory, filename), 'r')
    ctx.variable = filename.split('_')[0]
    if data.project_id == 'CORDEX':
        ctx.realm = 'atmos'
    else:
        if 'modeling_realm' in data.ncattrs():
            ctx.realm = data.modeling_realm
        else:
            raise Exception('"modeling_realm" attribute is missing.')
    if 'frequency' in data.ncattrs():
        ctx.frequency = data.frequency
    else:
        raise Exception('"frequency" attribute is missing.')
    if 'units' in data.variables['time'].ncattrs():
            ctx.tunits = control_time_units(data.variables['time'].units, ctx)
    else:
        raise Exception('"units" attribute is missing for "time" variable.')
    ctx.funits = convert_time_units(ctx.tunits, ctx.frequency)
    if 'calendar' in data.variables['time'].ncattrs():
        ctx.calendar = data.variables['time'].calendar
    else:
        raise Exception('"calendar" attribute is missing for "time" variable.')
    if ctx.calendar == 'standard' and data.model_id == 'CMCC-CM':
        ctx.calendar = 'proleptic_gregorian'
    data.close()
    ctx.instant = is_instant_time_axis(ctx)
    logging.warning('Frequency:'.ljust(25)+'{0}'.format(ctx.frequency))
    logging.warning('Calendar:'.ljust(25)+'{0}'.format(ctx.calendar))
    logging.warning('Time units:'.ljust(25)+'{0}'.format(ctx.tunits))
    logging.warning('Instant time axis:'.ljust(25)+'{0}'.format(ctx.instant))


def control_time_units(tunits, ctx):
    """
    Controls the time units format as at least "days since YYYY-MM-DD".
    The time units can be forced within configuration file using the ``time_units_default`` option.

    :param str tunits: The NetCDF time units string from file
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The appropriate time units string formatted and controlled depending on the project
    :rtype: *str*

    """
    units = tunits.split()
    units[0] = unicode('days')
    if len(units[2].split('-')) == 1:
        units[2] = units[2] + '-{0}-{1}'.format('01', '01')
    elif len(units[2].split('-')) == 2:
        units[2] = units[2] + '-{0}'.format('01')
    try:
        time_units_default = eval(ctx.cfg.get(ctx.project, 'time_units_default'))
        if ' '.join(units) != time_units_default:
            logging.warning('Invalid time units. '
                            'Replace "{0}" by "{1}"'.format(' '.join(units),
                                                            time_units_default))
        return time_units_default
    except:
        return ' '.join(units)


def convert_time_units(unit, frequency):
    """
    Converts default time units from file into time units using the MIP frequency.
    As en example, for a 3-hourly file, the time units "days since YYYY-MM-DD" becomes
    "hours since YYYY-MM-DD".

    :param str tunits: The NetCDF time units string from file
    :param str frequency: The time frequency
    :returns: The converted time units string
    :rtype: *str*

    """
    units = {'subhr': 'minutes',
             '3hr': 'hours',
             '6hr': 'hours',
             'day': 'days',
             'mon': 'months',
             'yr': 'years'}
    return unit.replace('days', units[frequency])


def counted(fct):
    """
    Decorator used to count all file process calls.

    :param callable fct: The function to monitor
    :returns: A wrapped function with a ``.called`` attribute
    :rtype: *callable*

    """
    @wraps(fct)  # Convenience decorator to keep the file_process docstring
    def wrapper(*args, **kwargs):
        wrapper.called += 1
        return fct(*args, **kwargs)
    wrapper.called = 0
    wrapper.__name__ = fct.__name__
    return wrapper


@counted
def time_axis_processing(inputs):
    """
    time_axis_processing(inputs)

    Time axis process that\:
     * Deduces start and end dates from filename,
     * Rebuilds the theoretical time axis (using frenquency, calendar, etc.),
     * Compares the theoretical time axis with the time axis from the file,
     * Compares the last theoretical date with the end date from the filename,
     * Checks if the expected time units keep unchanged,
     * Checks the squareness and the consistency of time boundaries,
     * Rewrites (with ``-w/--write`` mode) the new time axis,
     * Computes the new checksum if modified,
     * Tracebacks the status.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The time axis status as an :func:`AxisStatus` instance
    :rtype: *dict*

    """
    # Extract inputs from tuple
    filename, ctx = inputs
    # Extract start and end dates from filename
    start_date, end_date = dates_from_filename(filename, ctx)
    start = Date2num(start_date, units=ctx.funits, calendar=ctx.calendar)
    # Set time length, True/False instant axis and incrementation in frequency units
    data = Dataset('{0}/{1}'.format(ctx.directory, filename), 'r+')
    length = data.variables['time'].shape[0]
    inc = time_inc(ctx.frequency)
    # Instanciates object to display axis status
    status = AxisStatus()
    status.directory = ctx.directory
    status.file = filename
    status.start = date_print(start_date)
    status.end = date_print(end_date)
    status.steps = length
    status.calendar = ctx.calendar
    status.instant = ctx.instant
    status.units = control_time_units(data.variables['time'].units, ctx)
    # Rebuild a proper time axis
    axis_hp, last_hp = rebuild_time_axis(start, length, inc, ctx)  # High precision
    # Low precision avoiding float precision issues
    axis_lp, last_lp = rebuild_time_axis(trunc(start, 5), length, inc, ctx)
    # Check consistency between last time date and end date from filename
    if not last_date_checker(date_print(last_hp), date_print(end_date)) and \
       not last_date_checker(date_print(last_lp), date_print(end_date)):
        status.control.append('003')
        logging.warning('ERROO3 - {0} - The date from last theoretical time step differs from '
                        'the end date from filename'.format(filename))
        status.axis = axis_lp
        status.last = date_print(last_lp)
        return status
    # Set appropriate float precision
    if last_date_checker(date_print(last_hp), date_print(end_date)):
        status.last = date_print(last_hp)
        status.axis = axis_hp
    elif last_date_checker(date_print(last_lp), date_print(end_date)):
        status.last = date_print(last_lp)
        status.axis = axis_lp
    # Check inconsistency between instant time and time boundaries
    if ctx.instant and ('time_bnds' in data.variables.keys()):
        status.control.append('004')
        logging.warning('ERROO4 - {0} - An instantaneous time axis should not embeded time '
                        'boundaries'.format(filename))
        # Delete time bounds and bounds attribute from file if write of force mode
        if ctx.write or ctx.force:
            if 'bounds' in data.variables['time'].ncattrs():
                del data.variables['time'].bounds
            data.close()
            nc_var_delete(ctx, filename, 'time_bnds')
            data = Dataset('{0}/{1}'.format(ctx.directory, filename), 'r+')
    # Control consistency between averaged time and time boundaries
    if not ctx.instant and ('time_bnds' not in data.variables.keys()):
        status.control.append('005')
        logging.warning('ERROO5 - {0} - An averaged time axis should embeded time '
                        'boundaries'.format(filename))
        status.axis = axis_lp
        status.last = date_print(last_lp)
        return status
    # Check time axis squareness
    status.time = data.variables['time'][:]
    if time_checker(status.axis, status.time):
        status.control.append('000')
    else:
        status.control.append('001')
        logging.warning('ERROO1 - {0} - Mistaken time axis over one or several time '
                        'steps'.format(filename))
    # Rebuild, read and check time boundaries squareness if needed
    if 'time_bnds' in data.variables.keys():
        axis_bnds = rebuild_time_bnds(start, length, inc, ctx)
        time_bnds = data.variables['time_bnds'][:, :]
        status.bnds = time_checker(axis_bnds, time_bnds)
    # Rewrite time axis depending on checking
    if (ctx.write and not time_checker(status.axis, status.time)) or ctx.force:
        data.variables['time'][:] = status.axis
        # Rewrite time units according to MIP requirements (i.e., same units for all files)
        data.variables['time'].units = ctx.tunits
        # Rewrite time boundaries if needed
        if 'time_bnds' in data.variables.keys():
            data.variables['time_bnds'][:, :] = axis_bnds
    # Control consistency between time units
    if ctx.tunits != status.units:
        status.control.append('002')
        logging.warning('ERROO2 - {0} - Time units must be unchanged for '
                        'the same dataset.'.format(filename))
    # Close file
    data.close()
    # Compute checksum at the end of all modifications and after closing file
    if (ctx.write or ctx.force) and '000' not in status.control:
        status.checksum = checksum(ctx, filename)
    # Return file status
    return status


def checksum(ctx, filename):
    """
    Does the MD5 or SHA256 checksum by the Shell avoiding Python memory limits.

    :param str file: The full path of a file
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If the checksum fails

    """
    assert (ctx.checksum in ['SHA256', 'MD5']), 'Invalid checksum type: {0} instead of \
    MD5 or SHA256'.format(ctx.checksum)
    ffp = '{0}/{1}'.format(ctx.directory, filename)
    try:
        if ctx.checksum == 'SHA256':
            shell = os.popen("sha256sum {0} | awk -F ' ' '{{ print $1 }}'".format(ffp), 'r')
        elif ctx.checksum == 'MD5':
            shell = os.popen("md5sum {0} | awk -F ' ' '{{ print $1 }}'".format(ffp), 'r')
        return shell.readline()[:-1]
    except:
        raise Exception('Checksum failed for {0}'.format(ffp))


def nc_var_delete(ctx, filename, variable):
    """
    Delete a NetCDF variable using NCO operators.
    A unique filename is generated to avoid multithreading errors.
    To overwrite the input file, the source file is dump using the ``cat`` Shell command-line
    to avoid Python memory limit.

    :param str filename: The filename
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :param str variable: The NetCDF variable to delete
    :raises Error: If the deletion failed

    """
    # Generate unique filename
    tmp = '{0}{1}'.format(str(uuid4()), '.nc')
    try:
        os.popen("ncks -x -O -v {3} {0}/{1} {0}/{2}".format(ctx.directory,
                                                            filename,
                                                            tmp,
                                                            variable), 'r')
        os.popen("cat {0}/{2} > {0}/{1}".format(ctx.directory,
                                                filename,
                                                tmp,
                                                variable), 'r')
        os.remove('{0}/{1}'.format(ctx.directory, tmp))
    except:
        os.remove('{0}/{1}'.format(ctx.directory, tmp))
        raise Exception('Deleting "{0}" failed for {1}'.format(variable, file))


def dates_from_filename(filename, ctx):
    """
    Returns datetime objetcs for start and end dates from the filename.
    To rebuild a proper time axis, the dates from filename are expected to set the first
    time boundary and not the middle of the time interval.

    :param str filename: The filename
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)

    :returns: ``datetime`` instances for start and end dates from the filename
    :rtype: *datetime.datetime*

    """
    dates = []
    for date in ctx.pattern.search(filename).groups()[-2:]:
        digits = untroncated_timestamp(date)
        # Convert string digits to %Y-%m-%d %H:%M:%S format
        date_as_since = ''.join([''.join(triple) for triple in
                        zip(digits[::2], digits[1::2], ['', '-', '-', ' ', ':', ':', ':'])])[:-1]
        # Use num2date to create netCDF4 datetime objects
        if ctx.frequency in ['3hr', '6hr']:
            # Fix on filename digits for 3hr and 6hr frequencies. 3hr (6hr) files always start
            # at 000000 end at 2100000 (180000) whether the time axis is instaneous or not.
            date_index = ctx.pattern.search(filename).groups()[-2:].index(date)
            if ctx.instant:
                date_correction = _INSTANT_TIME_CORRECTION[ctx.frequency][date_index][digits[-6:]]
                dates.append(num2date(date_correction,
                                      units='days since ' + date_as_since,
                                      calendar=ctx.calendar))
            else:
                date_correction = _AVERAGED_TIME_CORRECTION[ctx.frequency][date_index][digits[-6:]]
                dates.append(num2date(date_correction,
                                      units='days since ' + date_as_since,
                                      calendar=ctx.calendar))
        else:
            dates.append(num2date(0.0,
                         units='days since ' + date_as_since,
                         calendar=ctx.calendar))
    return dates


def untroncated_timestamp(timestamp):
    """
    Returns proper digits for yearly and monthly truncated timestamps.
    The dates from filename are filled with the 0 digit to reach 14 digits.
    Consequently, yealry dates starts at January 1st and monthly dates starts at first day
    of the month.

    :param str timestamp: A date string from a filename
    :returns: The filled timestamp
    :rtype: *str*

    """
    if len(timestamp) == 4:
        # Start year at january 1st
        return (timestamp+'0101').ljust(14, '0')
    elif len(timestamp) == 6:
        # Start month at first day
        return (timestamp+'01').ljust(14, '0')
    else:
        return timestamp.ljust(14, '0')


def Num2date(num_axis, units, calendar):
    """
    A wrapper from ``netCDF4.num2date`` able to handle "years since" and "months since" units.
    If time units are not "years since" or "months since", calls usual ``netcdftime.num2date``.

    :param array num_axis: The numerical time axis following units
    :param str units: The proper time units
    :param str calendar: The NetCDF calendar attribute
    :returns: The corresponding date axis
    :rtype: *array*

    """
    if not units.split(' ')[0] in ['years', 'months']:
        # If units are not 'years' or 'months since', call usual netcdftime.num2date:
        return num2date(num_axis, units=units, calendar=calendar)
    else:
        # Return to time refenence with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert the time refrence 'units_as_days' as datetime object
        start_date = num2date(0.0, units=units_as_days, calendar=calendar)
        # Control num_axis to always get an Numpy array (even with a scalar)
        num_axis_mod = np.atleast_1d(np.array(num_axis))
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering
            # the whole 'num_axis' period
            max_years = np.floor(np.max(num_axis_mod)) + 1
            min_years = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([add_year(start_date, years_to_add)
                                  for years_to_add in np.arange(min_years, max_years+2)])
            # Convert rebuilt years axis as 'number of days since'
            cdftime = utime(units_as_days, calendar=calendar)
            years_axis_as_days = cdftime.date2num(years_axis)
            # Index of each years
            yind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' addint the number of days since referenced time
            # with an half-increment (num_axis_mod - yind) = 0 or 0.5
            num_axis_mod_days = (years_axis_as_days[yind - int(min_years)] +
                                 (num_axis_mod - yind) *
                                 np.diff(years_axis_as_days)[yind - int(min_years)])
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.floor(np.max(num_axis_mod)) + 1
            min_months = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, months_to_add)
                                   for months_to_add in np.arange(min_months, max_months+12)])
            # Convert rebuilt months axis as 'number of days since'
            cdftime = utime(units_as_days, calendar=calendar)
            months_axis_as_days = cdftime.date2num(months_axis)
            # Index of each months
            mind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' addint the number of days since referenced time
            # with an half-increment (num_axis_mod - mind) = 0 or 0.5
            num_axis_mod_days = (months_axis_as_days[mind - int(min_months)] +
                                 (num_axis_mod - mind) *
                                 np.diff(months_axis_as_days)[mind - int(min_months)])
        # Convert result as date axis
        return num2date(num_axis_mod_days, units=units_as_days, calendar=calendar)


def Date2num(date_axis, units, calendar):
    """
    A wrapper from ``netCDF4.date2num`` able to handle "years since" and "months since" units.
    If time units are not "years since" or "months since" calls usual ``netcdftime.date2num``.

    :param array num_axis: The date axis following units
    :param str units: The proper time units
    :param str calendar: The NetCDF calendar attribute
    :returns: The corresponding numerical time axis
    :rtype: *array*

    """
    # date_axis is the date time axis incremented following units (i.e., by years, months, etc).
    if not units.split(' ')[0] in ['years', 'months']:
        # If units are not 'years' or 'months since', call usual netcdftime.date2num:
        return date2num(date_axis, units=units, calendar=calendar)
    else:
        # Return to time refenence with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert date axis as number of days since time reference
        days_axis = date2num(date_axis, units=units_as_days, calendar=calendar)
        # Convert the time refrence 'units_as_days' as datetime object
        start_date = num2date(0.0, units=units_as_days, calendar=calendar)
        # Create years axis from input date axis
        years = np.array([date.year for date in np.atleast_1d(np.array(date_axis))])
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering
            # the whole 'num_axis' period
            max_years = np.max(years - start_date.year) + 1
            min_years = np.min(years - start_date.year) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([add_year(start_date, yid)
                                  for yid in np.arange(min_years, max_years+2)])
            # Convert years axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            years_axis_as_days = cdftime.date2num(years_axis)
            # Find closest index for years_axis_as_days in days_axis
            closest_index = np.searchsorted(years_axis_as_days, days_axis)
            # ???
            NUM = days_axis - years_axis_as_days[closest_index]
            DEN = np.diff(years_axis_as_days)[closest_index]
            return min_years + closest_index + NUM / DEN
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering
            # the whole 'num_axis' period
            max_months = np.max(12 * (years - start_date.year)) + 1
            min_months = np.min(12 * (years - start_date.year)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([add_month(start_date, mid)
                                   for mid in np.arange(min_months, max_months+12)])
            # Convert months axis as number of days since time reference
            cdftime = utime(units_as_days, calendar=calendar)
            months_axis_as_days = cdftime.date2num(months_axis)
            # Find closest index for months_axis_as_days in days_axis
            closest_index = np.searchsorted(months_axis_as_days, days_axis)
            # ???
            NUM = days_axis - months_axis_as_days[closest_index]
            DEN = np.diff(months_axis_as_days)[closest_index]
            return min_months + closest_index + NUM / DEN


def add_month(date, months_to_add):
    """
    Finds the next month from date.

    :param datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int months_to_add: The number of months to add to the date
    :returns: The final date
    :rtype: *datetime*

    """
    years_to_add = int((date.month+months_to_add - np.mod(date.month+months_to_add - 1, 12) - 1)
                       / 12)
    new_month = int(np.mod(date.month+months_to_add - 1, 12)) + 1
    new_year = date.year + years_to_add
    date_next = phony_datetime(year=new_year,
                               month=new_month,
                               day=date.day,
                               hour=date.hour,
                               minute=date.minute,
                               second=date.second)

    return date_next


def add_year(date, years_to_add):
    """
    Finds the next year from date.

    :param datetime date: Accepts datetime or phony datetime from ``netCDF4.num2date``.
    :param int years_to_add: The number of years to add to the date
    :returns: The final date
    :rtype: *datetime*

    """
    new_year = date.year + years_to_add
    date_next = phony_datetime(year=new_year,
                               month=date.month,
                               day=date.day,
                               hour=date.hour,
                               minute=date.minute,
                               second=date.second)
    return date_next


def is_instant_time_axis(ctx):
    """
    Deduces from MIP frequency, variable and realm, if the file requires an instantaneous
    time axis.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: True if the file requires an instantaneous time axis
    :rtype: *boolean*

    """
    need_instant_time = eval(ctx.cfg.get(ctx.project,
                                         'need_instant_time'))
    return (ctx.variable, ctx.frequency, ctx.realm) in need_instant_time


def time_inc(frequency):
    """
    Returns the time incrementation depending on the MIP frequency.

    :param str frequency: The MIP frequency
    :returns: The corresponding time raising value
    :rtype: *int*

    """
    inc = {'subhr': 30,
           '3hr': 3,
           '6hr': 6,
           'day': 1,
           'mon': 1,
           'yr': 1}
    return inc[frequency]


def date_print(date):
    """
    Prints date in format: %Y%m%d %H:%M:%s.

    :param datetime date: Accepts datetime or phony datetime objects
    :returns: The corresponding formatted date to print
    :rtype: *str*

    """
    return '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(date.year,
                                                                    date.month,
                                                                    date.day,
                                                                    date.hour,
                                                                    date.minute,
                                                                    date.second)


def rebuild_time_axis(start, length, inc, ctx):
    """
    Rebuilds time axis from date axis, depending on MIP frequency, calendar and instant status.

    :param float date: The numerical date to start (from ``netCDF4.num2date`` or :func:`Date2num`)
    :param int length: The time axis length (i.e., the timesteps number)
    :param int inc: The time incrementation (from :func:`time_inc`)
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The corresponding theoretical time axis
    :rtype: *float array*

    """
    date_axis, last = rebuild_date_axis(start,
                                        length,
                                        inc,
                                        ctx)
    axis = Date2num(date_axis,
                    units=ctx.tunits,
                    calendar=ctx.calendar)
    return axis, last


def rebuild_date_axis(start, length, inc, ctx):
    """
    Rebuilds date axis from numerical time axis, depending on MIP frequency, calendar and
    instant status.

    :param float date: The numerical date to start (from ``netCDF4.date2num`` or :func:`Date2num`)
    :param int length: The time axis length (i.e., the timesteps number)
    :param int inc: The time incrementation (from :func:`time_inc`)
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)

    :returns: The corresponding theoretical date axis
    :rtype: *datetime array*

    """
    num_axis = np.arange(start=start,
                         stop=start + length * inc,
                         step=inc)
    if ctx.funits.split(' ')[0] in ['years', 'months']:
        last = Num2date(num_axis[-1],
                        units=ctx.funits,
                        calendar=ctx.calendar)[0]
    else:
        last = Num2date(num_axis[-1],
                        units=ctx.funits,
                        calendar=ctx.calendar)
    if not ctx.instant:
        num_axis += 0.5 * inc
    date_axis = Num2date(num_axis,
                         units=ctx.funits,
                         calendar=ctx.calendar)
    return date_axis, last


def trunc(f, n):
    """
    Truncates a float f to n decimal places before rounding

    :param float f: The number to truncates
    :param int n: Decimal number to place before rounding
    :returns: The corresponding truncated number
    :rtype: *float*

    """
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])


def time_checker(right_axis, test_axis):
    """
    Tests the time axis squareness.

    :param array right_axis: The theoretical time axis (from :func:`rebuild_time_axis`),
    :param array test_axis: The time axis to check from NetCDF file,
    :returns: True if both time axis are exactly the same,
    :rtype: *boolean*

    """
    return np.array_equal(right_axis, test_axis)


def rebuild_time_bnds(start, length, inc, ctx):
    """
    Rebuilds time boundaries from the start date, depending on MIP frequency, calendar and
    instant status.

    :param float date: The numerical date to start (from ``netCDF4.date2num`` or :func:`Date2num`)
    :param int length: The time axis length (i.e., the timesteps number)
    :param int inc: The time incrementation (from :func:`time_inc`)
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance).

    :returns: The corresponding theoretical time boundaries
    :rtype: *[n, 2] array*

    """
    num_axis_bnds = np.column_stack(((np.arange(start=start,
                                                stop=start + length * inc,
                                                step=inc)),
                                     (np.arange(start=start,
                                                stop=start + (length+1) * inc,
                                                step=inc)[1:])))
    date_axis_bnds = Num2date(num_axis_bnds,
                              units=ctx.funits,
                              calendar=ctx.calendar)
    axis_bnds = Date2num(date_axis_bnds,
                         units=ctx.tunits,
                         calendar=ctx.calendar)
    return axis_bnds


def last_date_checker(last, end):
    """
    Checks if last and end date are the same.

    :param float last: The last timesteps of the theoretical time axis \
    (from :func:`rebuild_time_axis`)
    :param float end: The numerical date to end (from ``netCDF4.date2num`` or :func:`Date2num`)
    :returns: True if both dates are exactly the same
    :rtype: *boolean*

    """
    return last == end


def yield_inputs(ctx):
    """
    Yields all files to process within tuples with the processing context.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for filename in sorted(os.listdir(ctx.directory)):
        if not re.match(ctx.pattern, filename):
            logging.warning('{0} has invalid filename and was skipped'.format(filename))
            continue
        yield filename, ctx


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`time_axis_processing` call
    :rtype: *callable*
    :raises Error: When a thread-process failed preserving its traceback

    """
    try:
        return time_axis_processing(inputs)
    except:
        logging.exception('A thread-process fails:')


def run(job=None):
    """
    Main process that\:
     * Instanciates processing context,
     * Defines the referenced time properties,
     * Instanciates threads pools,
     * Prints or logs the time axis diagnostics.

    :param dict job: An optionnal dictionnary to supply instead of classical command-line use.

    """
    # Instanciate processing context from command-line arguments or SYNDA job dictionnary
    ctx = ProcessingContext(get_args(job))
    if ('/fx/' or '/fixed/') in ctx.directory:
        logging.warning('Skipped "fx/fixed" frequency because no time axis')
    else:
        logging.info('Time diagnostic started for {0}'.format(ctx.directory))
        # Set driving time properties (calendar, frequency and time units)
        # from first file in directory
        time_init(ctx)
        nfiles = len(glob('{0}/*.nc'.format(ctx.directory)))
        logging.info('Files to process:'.ljust(25)+'{0}'.format(nfiles))
        # Process
        pool = ThreadPool(int(ctx.cfg.defaults()['threads_number']))
        outputs = pool.imap(wrapper, yield_inputs(ctx))
        # Returns diagnostic for each file
        if not job:
            job = {}
        job['files'] = {}
        for output in outputs:
            logging.info('==> Filename:'.ljust(25)+'{0}'.format(output.file))
            logging.info('-> Start:'.ljust(25)+'{0}'.format(str(output.start)))
            logging.info('-> End:'.ljust(25)+'{0}'.format(str(output.end)))
            logging.info('-> Last:'.ljust(25)+'{0}'.format(str(output.last)))
            logging.info('-> Timesteps:'.ljust(25)+'{0}'.format(output.steps))
            logging.info('-> Time axis status:'.ljust(25)+'{0}'.format(','.join(output.control)))
            logging.info('-> Time boundaries:'.ljust(25)+'{0}'.format(output.bnds))
            logging.info('-> New checksum:'.ljust(25)+'{0}'.format(output.checksum))
            if ctx.verbose:
                logging.info('-> Time axis:')
                logging.info('{0}'.format(fill(' | '.join(map(str,
                                                              output.time.tolist())),
                                               width=100)))
                logging.info('-> Theoretical axis:')
                logging.info('{0}'.format(fill(' | '.join(map(str,
                                                              output.axis.tolist())),
                                               width=100)))
            # Return diagnostic to SYNDA using job dictionnary
            job['files'][output.file] = {}
            job['files'][output.file]['calendar'] = output.calendar
            job['files'][output.file]['start'] = output.start
            job['files'][output.file]['end'] = output.end
            job['files'][output.file]['last'] = output.last
            job['files'][output.file]['length'] = output.steps
            job['files'][output.file]['instant'] = output.instant
            job['files'][output.file]['bnds'] = output.bnds
            job['files'][output.file]['status'] = ','.join(output.control)
            job['files'][output.file]['new_checksum'] = output.checksum
        # Close tread pool
        pool.close()
        pool.join()
        logging.info('Time diagnostic completed '
                     '({0} files scanned)'.format(time_axis_processing.called))
        return job


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
