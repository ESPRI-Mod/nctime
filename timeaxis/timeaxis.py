#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

# Module imports
import re
import sys
import os
import argparse
import logging
import numpy as np
from datetime import datetime
from functools import wraps
from netCDF4 import Dataset
from textwrap import fill
from multiprocessing.dummy import Pool as ThreadPool
from utils import init_logging, config_parse, check_directory, MultilineFormatter, trunc
from file_handler import File, _date2num, _num2date
import db

# Program version
__version__ = 'v{0} {1}'.format('3.7', datetime(year=2016, month=07, day=06).strftime("%Y-%d-%m"))

# Incrementation depending on MIP table
__INC__ = {'subhr': 30, '3hr': 3, '6hr': 6, 'day': 1, 'mon': 1, 'yr': 1}


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

    :param *ArgumentParser* args: Parsed command-line arguments
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
        self.db = args.db
        self.verbose = args.v
        cfg = config_parse(args.i)
        if args.project in cfg.sections():
            self.project = args.project
        else:
            raise Exception('No section in configuration file corresponds to "{0}" project. \
                            Supported projects are {1}.'.format(args.project,
                                                                cfg.sections()))
        if self.db and cfg.has_option('DEFAULT', 'db_path'):
            self.db = cfg.get('DEFAULT', 'db_path')
        self.checksum_type = str(cfg.defaults()['checksum_type'])
        self.threads = int(cfg.defaults()['threads_number'])
        self.pattern = re.compile(cfg.get(self.project, 'filename_format'))
        self.need_instant = eval(cfg.get(self.project, 'need_instant_time'))
        self.tunits_default = None
        if cfg.has_option('time_units_default', self.project):
            self.tunits_default = cfg.get(self.project, 'time_units_default')
        self.ref = self.get_files_list().next()
        self.variable = unicode(self.ref.split('_')[0])

    def get_files_list(self):
        """
        Yields all files into a directory.

        :returns: A file iterator
        :rtype: *iter*

        """
        for filename in sorted(os.listdir(self.directory)):
            if ('_fx_' or '_fixed_') in filename:
                logging.warning('STOP because "fx/fixed" frequency has no time axis')
                sys.exit(0)
            if not re.match(self.pattern, filename):
                logging.warning('{0} has invalid filename and was skipped'.format(filename))
                continue
            yield filename


class TimeInit(object):
    """
    Encapsulates the time properties from first file into processing context.
    These properties has to be used as reference for all file into the directory.

     * The calendar, the frequency and the realm are read from NetCDF global attributes and
     use to detect instantaneous time axis,
     * The NetCDF time units attribute has to be unchanged in respect with CF convention and
     archives designs.

    +-------------------+-------------+---------------------------------+
    | Attribute         | Type        | Description                     |
    +===================+=============+=================================+
    | *self*.calendar   | *str*       | NetCDF calendar attribute       |
    +-------------------+-------------+---------------------------------+
    | *self*.frequency  | *str*       | NetCDF frequency attribute      |
    +-------------------+-------------+---------------------------------+
    | *self*.realm      | *str*       | NetCDF modeling realm attribute |
    +-------------------+-------------+---------------------------------+
    | *self*.tunits     | *str*       | Time units from file            |
    +-------------------+-------------+---------------------------------+
    | *self*.funits     | *str*       | Time units from frequency       |
    +-------------------+-------------+---------------------------------+
    | *self*.is_instant | *boolean*   | True if instantaneous axis      |
    +-------------------+-------------+---------------------------------+
    | *self*.has_bounds | *boolean*   | True if require time bounds     |
    +-------------------+-------------+---------------------------------+

    :raises Error: If NetCDF time units attribute is missing
    :raises Error: If NetCDF frequency attribute is missing
    :raises Error: If NetCDF realm attribute is missing
    :raises Error: If NetCDF calendar attribute is missing

    """
    def __init__(self, ctx):
        f = Dataset('{directory}/{ref}'.format(**ctx.__dict__), 'r')
        # Get realm
        if f.project_id == 'CORDEX':
            self.realm = 'atmos'
        else:
            if 'modeling_realm' in f.ncattrs():
                self.realm = f.modeling_realm
            else:
                raise Exception('"modeling_realm" attribute is missing.')
        # Get frequency
        if 'frequency' in f.ncattrs():
            self.frequency = f.frequency
        else:
            raise Exception('"frequency" attribute is missing.')
        # Convert time units into frequency units
        if 'units' in f.variables['time'].ncattrs():
                self.tunits = control_time_units(f.variables['time'].units, ctx.tunits_default)
        else:
            raise Exception('"units" attribute is missing for "time" variable.')
        self.funits = convert_time_units(self.tunits, self.frequency)
        # Get calendar
        if 'calendar' in f.variables['time'].ncattrs():
            self.calendar = f.variables['time'].calendar
        else:
            raise Exception('"calendar" attribute is missing for "time" variable.')
        if self.calendar == 'standard' and f.model_id == 'CMCC-CM':
            self.calendar = 'proleptic_gregorian'
        # Get boolean on instantaneous time axis
        self.is_instant = False
        if (ctx.variable, self.frequency, self.realm) in ctx.need_instant:
            self.is_instant = True
        # Get boolean on time boundaries
        self.has_bounds = False
        if 'time_bnds' in f.variables.keys():
            self.has_bounds = True
        f.close()


def get_args():
    """
    Returns parsed command-line arguments. See ``time_axis -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace
    :rtype: *ArgumentParser*

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
                    001: Corrected time axis because wrong time steps,|n
                    002: Corrected time axis because of changing time units,|n
                    003: Ignored time axis because of inconsistency between last date of time axis
                     and end date of filename period (e.g., wrong time axis length),|n
                    004: Corrected time axis deleting time boundaries for instant time,|n
                    005: Ignored averaged time axis without time boundaries,|n
                    006: Corrected time bounds because wrong time steps.|n|n

                    See full documentation on http://cmip5-time-axis.readthedocs.org/|n|n

                    The default values are displayed next to the corresponding flags.""",
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""Developed by:|n
               Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)|n
               Laliberte, F. (ExArch - frederic.laliberte@utoronto.ca)""")
    parser._optionals.title = "Optional arguments"
    parser._positionals.title = "Positional arguments"
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
        '--db',
        metavar='<db_path>',
        type=str,
        nargs='?',
        const='{0}/{1}'.format(os.getcwd(), 'timeaxis.db'),
        help="""SQLite database path to persist diagnostics. Default is|n
             <db_path> from config.ini. If no <db_path>, current|n
             working directory is used. If not, time diagnostic is not|n
             saved.""")
    parser.add_argument(
        '--log',
        metavar='$PWD',
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
    return parser.parse_args()


def control_time_units(tunits, tunits_default=None):
    """
    Controls the time units format as at least "days since YYYY-MM-DD".
    The time units can be forced within configuration file using the ``time_units_default`` option.

    :param str tunits: The NetCDF time units string from file
    :param tunits_default: The default time units that should be used
    :returns: The appropriate time units string formatted and controlled depending on the project
    :rtype: *str*

    """
    units = tunits.split()
    units[0] = unicode('days')
    if len(units[2].split('-')) == 1:
        units[2] += '-{0}-{1}'.format('01', '01')
    elif len(units[2].split('-')) == 2:
        units[2] += '-{0}'.format('01')
    if tunits_default and ' '.join(units) != tunits_default:
        logging.warning('Invalid time units. Replace "{0}" by "{1}"'.format(' '.join(units), tunits_default))
        return tunits_default
    else:
        return ' '.join(units)


def convert_time_units(tunits, frequency):
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
    return tunits.replace('days', units[frequency])


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
def process(inputs):
    """
    time_axis_processing(inputs)

    Time axis process that\:
     * Deduces start and end dates from filename,
     * Rebuilds the theoretical time axis (using frequency, calendar, etc.),
     * Compares the theoretical time axis with the time axis from the file,
     * Compares the last theoretical date with the end date from the filename,
     * Checks if the expected time units keep unchanged,
     * Checks the squareness and the consistency of time boundaries,
     * Rewrites (with ``--write`` mode) the new time axis,
     * Computes the new checksum if modified,
     * Traceback the status.

    :param tuple inputs: A tuple with the filename, the processing context and the time initialization
    :returns: The time axis status as an :func:`AxisStatus` instance
    :rtype: *dict*

    """
    # Extract processing context and time initialization from input tuple
    filename, ctx, init = inputs

    # Instantiate file handle from input tuple
    handler = File(directory=ctx.directory,
                   filename=filename,
                   has_bounds=init.has_bounds)

    # Extract start and end dates from filename
    start, _ = handler.get_start_end_dates(pattern=ctx.pattern,
                                           frequency=init.frequency,
                                           units=init.funits,
                                           calendar=init.calendar,
                                           is_instant=init.is_instant)

    # Rebuild a theoretical time axis with high precision
    handler.time_axis_rebuilt = handler.build_time_axis(start=start,
                                                        inc=__INC__[init.frequency],
                                                        input_units=init.funits,
                                                        output_units=init.tunits,
                                                        calendar=init.calendar,
                                                        is_instant=init.is_instant)

    # Check consistency between last time date and end date from filename
    if handler.last_date != handler.end_date:
        # Rebuild a theoretical time axis with low precision
        handler.time_axis_rebuilt = handler.build_time_axis(start=trunc(start, 5),
                                                            inc=__INC__[init.frequency],
                                                            input_units=init.funits,
                                                            output_units=init.tunits,
                                                            calendar=init.calendar,
                                                            is_instant=init.is_instant)
        if handler.last_date != handler.end_date:
            handler.status.append('003')
            logging.error('{0} - 003 - Last time step differs from end date from filename'.format(filename))
            if ctx.verbose:
                axe = fill(' | '.join(map(str, handler.time_axis.tolist())), width=100)
                logging.info('{0} - Time axis:\n {1}'.format(filename, axe))
                axe = fill(' | '.join(map(str, handler.time_axis_rebuilt.tolist())), width=100)
                logging.info('{0} - Theoretical axis:\n {1}'.format(filename, axe))
            return handler

    # Check consistency between instant time and time boundaries
    if init.is_instant and init.has_bounds:
        handler.status.append('004')
        logging.error('{0} - 004 - An instantaneous time axis should not embed time boundaries'.format(filename))

    # Check consistency between averaged time and time boundaries
    if not init.is_instant and not init.has_bounds:
        handler.status.append('005')
        logging.error('{0} - 005 - An averaged time axis should embed time boundaries'.format(filename))

    # Check time axis squareness
    if not np.array_equal(handler.time_axis_rebuilt, handler.time_axis):
        handler.status.append('001')
        logging.error('{0} - 001 - Mistaken time axis over one or several time steps'.format(filename))
    else:
        handler.status.append('000')
        logging.info('{0} - Time axis seems OK'.format(filename))

    # Check time boundaries squareness if needed
    if init.has_bounds:
        handler.time_bounds_rebuilt = handler.build_time_bounds(start=trunc(start, 5),
                                                                inc=__INC__[init.frequency],
                                                                input_units=init.funits,
                                                                output_units=init.tunits,
                                                                calendar=init.calendar)
        if not np.array_equal(handler.time_bounds_rebuilt, handler.time_bounds):
            handler.status.append('006')
            logging.error('{0} - 006 - Mistaken time bounds over one or several time steps'.format(filename))

    # Check consistency between time units
    if init.tunits != handler.time_units:
        handler.status.append('002')
        logging.error('{0} - 002 - Time units must be unchanged for the same dataset.'.format(filename))

    # Rewrite time axis depending on checking
    if (ctx.write or ctx.force) and set(['004']).intersection(set(handler.status)):
        # Delete time bounds and bounds attribute from file if write of force mode
        handler.nc_var_delete(variable='time_bnds')
        handler.nc_att_delete(attribute='bounds', variable='time')

    # Rewrite time axis depending on checking
    if (ctx.write and set(['001', '002', '006']).intersection(set(handler.status))) or ctx.force:
        handler.nc_var_overwrite('time', handler.time_axis_rebuilt)
        handler.nc_att_overwrite('units', 'time', init.tunits)
        # Rewrite time boundaries if needed
        if init.has_bounds:
            handler.nc_var_overwrite('time_bnds', handler.time_bounds_rebuilt)

    # Compute checksum at the end of all modifications and after closing file
    if (ctx.write or ctx.force) and set(['001', '002', '004', '006']).intersection(set(handler.status)):
        handler.new_checksum = handler.checksum(ctx.checksum_type)

    # Return file status
    return handler


def yield_inputs(ctx, tinit):
    """
    Yields all files to process within tuples with the processing context and the time initialization.

    :param ProcessingContext ctx: A :func:`ProcessingContext` class instance
    :param TimeInit tinit: A :func:`TimeInit` class instance
    :returns: Attach the processing context and the time initialization to a file processing as an iterator of tuples
    :rtype: *iter*

    """
    for filename in ctx.get_files_list():
        yield filename, ctx, tinit


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`process` call
    :rtype: *callable*
    :raises Error: When a thread-process failed preserving its traceback

    """
    try:
        return process(inputs)
    except:
        logging.exception('A thread-process fails:')


def run():
    """
    Main process that\:
     * Instanciates processing context,
     * Defines the referenced time properties,
     * Instanciates threads pools,
     * Prints or logs the time axis diagnostics.

    """
    # Instantiate processing context from command-line arguments
    ctx = ProcessingContext(get_args())
    logging.info('Time diagnostic started for {0}'.format(ctx.directory))
    # Set driving time properties (e.g., calendar, frequency and time units) from first file in directory
    tinit = TimeInit(ctx)
    # Process
    pool = ThreadPool(ctx.threads)
    handlers = pool.imap(wrapper, yield_inputs(ctx, tinit))
    # Persist diagnostics into database
    if ctx.db:
        # Check if database exists
        if not os.path.isfile(ctx.db):
            logging.warning('Database does not exist')
            db.create(ctx.db)
        # Commit each diagnostic as a new entry
        for handler in handlers:
            diagnostic = dict()
            diagnostic['creation_date'] = datetime.now()
            diagnostic.update(ctx.__dict__)
            diagnostic.update(tinit.__dict__)
            diagnostic.update(handler.__dict__)
            diagnostic['status'] = ','.join(handler.status)
            db.insert(ctx.db, diagnostic)
            logging.info('{0} - Diagnostic persisted into database'.format(handler.filename))
            if ctx.verbose:
                logging.info('-> Filename: {0}'.format(handler.filename))
                logging.info('Start: {0}'.format(handler.start_date))
                logging.info('End: {0}'.format(handler.end_date))
                logging.info('Last: {0}'.format(handler.last_date))
                logging.info('Time steps: {0}'.format(handler.length))
            if ctx.verbose:
                logging.info('-> Time axis:')
                logging.info('{0}'.format(fill(' | '.join(map(str, handler.time_axis.tolist())), width=100)))
                logging.info('-> Theoretical axis:')
                logging.info('{0}'.format(fill(' | '.join(map(str, handler.time_axis_rebuilt.tolist())), width=100)))
    # Close tread pool
    pool.close()
    pool.join()
    logging.info('Time diagnostic completed ({0} files scanned)'.format(process.called))
    sys.exit(0)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
