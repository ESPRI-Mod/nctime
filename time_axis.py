#!/usr/bin/env python
"""
.. module:: time_axis.py
   :platform: Unix
   :synopsis: Rewrite and/or check time axis of CMIP5 files upon local IPSL-ESGF datanode.

.. moduleauthor:: Levavasseur, G. <glipsl@ipsl.jussieu.fr>, Laliberte, F. <frederic.laliberte@utoronto.ca> and Raciazek, J. <Jerome.Raciazek@ipsl.jussieu.fr>

"""

# Module imports
import re, os, argparse, logging
from uuid import uuid4
import numpy as np
from argparse import RawTextHelpFormatter
from datetime import datetime
from netCDF4 import Dataset, date2num, num2date
from multiprocessing.dummy import Pool as ThreadPool
from netcdftime import datetime as phony_datetime
from textwrap import fill
from glob import glob

# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v2.1', '2015', '03', '27')

# Throttle upon number of threads to spawn
_THREAD_POOL_SIZE = 4

# Log levels
_LEVELS = {'debug': logging.error,
           'info': logging.info,
           'warning': logging.warning,
           'error': logging.error,
           'critical': logging.critical,
           'exception': logging.exception}



class _ProcessingContext(object):
    """Encapsulate processing context information for main process."""
    def __init__(self, args):
        _init_logging(args.logdir, args.outdiag)
        self.directory = _check_directory(args.directory)
        self.check = args.check
        self.write = args.write
        self.force = args.force
        self.verbose = args.verbose
        self.realm = None
        self.version = None
        self.frequency = None
        self.calendar = None
        self.tunits = None
        self.funits = None


class _SyndaProcessingContext(object):
    """Encapsulate processing context information for for synda call."""
    def __init__(self, full_path_variable):
        #_init_logging(args.logdir, args.outdiag) # Logger initiates by synda worker
        self.directory = _check_synda_directory(full_path_variable)
        self.check = True
        self.write = False
        self.force = False
        self.verbose = True
        self.realm = None
        self.version = None
        self.frequency = None
        self.calendar = None
        self.tunits = None
        self.funits = None


class _AxisStatus(object):
    """Encapsulate file information."""
    def __init__(self):
        self.directory = None
        self.file = None
        self.start = None
        self.end = None
        self.last = None
        self.steps = None
        self.instant = False
        self.frequency = None
        self.calendar = None
        self.tunits = None
        self.units = None
        self.control = []
        self.bnds = None
        self.checksum = None
        self.axis = None
        self.time = None


class _Exception(Exception):
    """Exception type to log encountered error."""
    def __init__(self, msg=''):
        self.msg = msg
    def __str__(self):
        print
        _log('error', self.msg)


def _get_args():
    """Returns parsed command line arguments."""
    parser=argparse.ArgumentParser(
                        description = """Rewrite and/or check CMIP5 file time axis on CICLAD filesystem, considering\n(i) uncorrupted filename period dates and\n(ii) properly-defined times units, time calendar and frequency NetCDF attributes.\n\nReturned status:\n000: Unmodified time axis,\n001: Corrected time axis because wrong timesteps.\n002: Corrected time axis because of changing time units,\n003: Ignored time axis because of inconsistency between last date of time axis and\nend date of filename period (e.g., wrong time axis length),\n004: Corrected time axis deleting time boundaries for instant time.""",
                        formatter_class = RawTextHelpFormatter,
                        add_help = False,
                        epilog = """Developped by Levavasseur, G. (CNRS/IPSL) and Laliberte, F. (ExArch)""")
    parser.add_argument('directory',
                        nargs = '?',
                        help = """Dataset path to browse following CMIP5 DRS\n(e.g., /prodigfs/esg/CMIP5/merge/NCAR/CCSM4/amip/day/atmos/cfDay/r7i1p1/v20130507/tas/).\n\n"""),
    parser.add_argument('-h', '--help',
                        action = "help",
                        help = """Show this help message and exit.\n\n""")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--check',
                        action = 'store_true',
                        default = True,
                        help = 'Check time axis squareness (default is True).\n\n')
    group.add_argument('-w', '--write',
                        action = 'store_true',
                        default = False,
                        help = """Rewrite time axis depending on checking\n(includes --check ; default is False).\nTHIS ACTION DEFINITELY MODIFY INPUT FILES!\n\n""")
    group.add_argument('-f', '--force',
                        action = 'store_true',
                        default = False,
                        help = """Force time axis writing overpassing checking step\n(default is False).\nTHIS ACTION DEFINITELY MODIFY INPUT FILES!\n\n""")
    parser.add_argument('-o', '--outdiag',
                        type = str,
                        nargs = '?',
                        const = '{0}/time_axis.diag'.format(os.getcwd()),
                        help = """Output diagnostic file (default is '{workdir}/time_axis.diag').\n\n""")
    parser.add_argument('-l', '--logdir',
                        type = str,
                        nargs = '?',
                        const = os.getcwd(),
                        help = """Logfile directory (default is working directory).\nIf not, standard output is used.\n\n""")
    parser.add_argument('-v', '--verbose',
                        action = 'store_true',
                        default = False,
                        help = 'Verbose mode.\n\n')
    parser.add_argument('-V', '--version',
                        action = 'version',
                        version = '%(prog)s ({0})'.format(__version__),
                        help = """Program version.""")
    return parser.parse_args()


def _check_directory(path):
    """Checks if supplied directroy exists """
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise _Exception('No such directory: {0}'.format(directory))
    # For main call fixed frequency raising error
    if directory.split('/')[8] == 'fx':
        raise _Exception('{0} frequency has no time axis'.format(directory.split('/')[8]))     
    return directory


def _check_synda_directory(path):
    """Checks if supplied directroy exists, if product is "process" and if frequency is not "fx"."""
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise _Exception('No such directory: {0}'.format(directory))
    if directory.split('/')[4] != 'process':
        raise _Exception('error', 'Product is "{0}" instead of "process"'.format(directory.split('/')[4]))
    # For synda call fixed frequency are skipped
    if directory.split('/')[8] == 'fx':
        _log('warning', '{0} frequency has no time axis: skipped'.format(directory.split('/')[8]))     
        return None
    return directory


def _get_unique_logfile(logdir):
    """Get unique logfile name."""
    logfile = 'time_axis-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    return os.path.join(logdir, logfile)


def _init_logging(logdir, outdiag):
    """Creates logfile or formates console message"""
    if logdir:
        if not os.path.exists(logdir): os.mkdir(logdir)
        logging.basicConfig(filename = _get_unique_logfile(logdir),
                            level = logging.DEBUG,
                            format = '%(asctime)s %(levelname)s %(message)s',
                            datefmt = '%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level = logging.DEBUG,
                            format = '%(message)s')
    if outdiag:
        diag = logging.FileHandler(filename = outdiag, mode = 'w')
        diag.setLevel(logging.DEBUG)
        diag.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger('').addHandler(diag)


def _log(level, msg):
    """Pointer to level logs."""
    return _LEVELS[level](msg)


def _time_init(ctx):
    """Returns required reference time properties, especially calendar to initialise CDMS calendar."""
    file = _get_file_list(ctx).next()[0]
    data = Dataset('{0}/{1}'.format(ctx.directory, file), 'r')
    ctx.frequency = ctx.directory.split('/')[8]
    ctx.version = os.path.realpath(ctx.directory).split('/')[12]
    ctx.tunits = _control_time_units(data.variables['time'].units)
    ctx.funits = _convert_time_units(ctx.tunits, ctx.frequency)
    ctx.realm = ctx.directory.split('/')[9]
    ctx.calendar = data.variables['time'].calendar
    if ctx.calendar == 'standard' and ctx.directory.split('/')[6] == 'CMCC-CM':
        ctx.calendar = 'proleptic_gregorian'
    data.close()
    _log('warning', 'Version = {0}'.format(ctx.version))
    _log('warning', 'Frequency = {0}'.format(ctx.frequency))
    _log('warning', 'Calendar = {0}'.format(ctx.calendar))
    _log('warning', 'Time units = {0}'.format(ctx.tunits))


def _get_file_list(ctx):
    """Yields sorted list of filenames in directory."""
    pattern = re.compile(r'([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\d]+)-([\d]+).nc')
    for file in sorted(os.listdir(ctx.directory)):
        if not re.match(pattern, file):
            _log('warning', '{0} has invalid filename: skipped'.format(file))
            continue
        yield file, ctx


def _control_time_units(tunits):
    """Control time units format as at least "days since YYYY-MM-DD"."""
    units = tunits.split()
    units[0] = unicode('days')
    if len(units[2].split('-')) == 1:
        units[2] = units[2] + '-{0}-{1}'.format('01','01')
    elif len(units[2].split('-')) == 2:
        units[2] = units[2] + '-{0}'.format('01')
    return ' '.join(units)


def _convert_time_units(unit, frequency):
    """Converts file default time units depending on frequency."""
    units = {'subhr':'minutes',
             '3hr':'hours',
             '6hr':'hours',
             'day':'days',
             'mon':'months',
             'yr' :'years'}
    return unit.replace('days', units[frequency])


def _time_axis_processing(inputs):
    """Time axis process in three step: rebuild, check and rewrite."""
    # Extract inputs from tuple
    filename, ctx = inputs
    # Extract start and end dates from filename
    start_date, end_date = _dates_from_filename(filename, ctx.calendar)
    start = _date2num(start_date, units = ctx.funits, calendar = ctx.calendar)
    # Set time length, True/False instant axis and incrementation in frequency units
    data = Dataset('{0}/{1}'.format(ctx.directory, filename), 'r+')
    length = data.variables['time'].shape[0]
    instant = _is_instant_time_axis(filename, ctx.realm)
    inc = _time_inc(ctx.frequency)
    # Instanciates object to display axis status
    status = _AxisStatus()
    status.directory = ctx.directory
    status.file = filename
    status.start = _date_print(start_date)
    status.end = _date_print(end_date)
    status.steps = length
    status.frequency = ctx.frequency
    status.calendar = ctx.calendar
    status.tunits = ctx.tunits
    status.units = _control_time_units(data.variables['time'].units)
    if instant:
        status.instant = True
    # Rebuild a proper time axis
    axis_hp, last_hp = _rebuild_time_axis(start, length, instant, inc, ctx) # High precision
    axis_lp, last_lp = _rebuild_time_axis(trunc(start, 5), length, instant, inc, ctx) # Low precision avoiding float precision issues
    # Control consistency between last time date and end date from filename
    if not _last_date_checker(_date_print(last_hp), _date_print(end_date)) and not _last_date_checker(_date_print(last_lp), _date_print(end_date)):
        status.control.append('003')
        _log('warning', 'ERROO3 - Inconsistent last and end dates for {0}'.format(ctx.filename))
    else:
        if _last_date_checker(_date_print(last_hp), _date_print(end_date)):
            status.last = _date_print(last_hp) ; status.axis = axis_hp
        elif _last_date_checker(_date_print(last_lp), _date_print(end_date)):
            status.last = _date_print(last_lp) ; status.axis = axis_lp
        # Control consistency between instant time and time boundaries
        if instant and ('time_bnds' in data.variables.keys()):
            status.control.append('004')
            _log('warning', 'ERROO4 - Inconsistent time_bnds with instant time for {0}'.format(ctx.filename))
            # Delete time bounds and bounds attribute from file
            if ctx.write or ctx.force:
                if 'bounds' in data.variables['time'].ncattrs():
                    del data.variables['time'].bounds
                data.close()
                _nc_var_delete(ctx, filename, 'time_bnds')
                # Compute checksum
                status.checksum = _checksum(ctx, filename)
                data = Dataset('{0}/{1}'.format(ctx.directory, filename), 'r+')
        # Check time axis squareness
        if ctx.check or ctx.write:
            status.time = data.variables['time'][:]
            if _time_checker(status.axis, status.time):
                status.control.append('000')
            else:
                status.control.append('001')
                _log('warning', 'ERROO1 - Wrong time axis for {0}'.format(ctx.filename))
            # Rebuild, read and check time boundaries squareness if needed
            if 'time_bnds' in data.variables.keys():
                axis_bnds = _rebuild_time_bnds(start, length, inc, ctx)
                time_bnds = data.variables['time_bnds'][:,:]
                if _time_checker(axis_bnds, time_bnds): status.bnds = True
                else: status.bnds = False
        # Rewrite time axis depending on checking
        if (ctx.write and not _time_checker(status.axis, status.time)) or ctx.force:
            data.variables['time'][:] = status.axis
            # Rewrite time units according to CMIP5 requirements (i.e., same units for all files)
            data.variables['time'].units = ctx.tunits
            # Rewrite time boundaries if needed
            if 'time_bnds' in data.variables.keys():
                data.variables['time_bnds'][:,:] = axis_bnds
            # Compute checksum
            status.checksum = _checksum(ctx, filename)
        # Control consistency between time units
        if ctx.tunits != status.units:
            status.control.append('002')
            _log('warning', 'ERROO2 - Changing time units for {0}'.format(ctx.filename))
    # Close file
    data.close()
    # Return file status
    return status


def _checksum(ctx, filename):
    """Do MD5 checksum by Shell"""
    try:
        shell = os.popen("md5sum {0} | awk -F ' ' '{{ print $1 }}'".format('{0}/{1}'.format(ctx.directory, filename)), 'r')
        return shell.readline()[:-1]
    except:
        raise _Exception('Checksum failed for {0}'.format('{0}/{1}'.format(ctx.directory, filename)))


def _nc_var_delete(ctx, filename, variable):
    """Delete NetCDF variable using NCO operators and overwrite input file."""
    # Generate unique filename to avoid multithreading errors
    tmp = '{0}{1}'.format(str(uuid4()), '.nc')
    try:
        os.popen("ncks -x -O -v {3} {0}{1} {0}{2}".format(ctx.directory, filename, tmp, variable), 'r')
        # Dumping source file using 'cat' Shell command-line to avoid Python memory limit
        os.popen("cat {0}{2} > {0}{1}".format(ctx.directory, filename, tmp, variable), 'r')
        os.remove('{0}{1}'.format(ctx.directory, tmp))
    except:
        os.remove('{0}{1}'.format(ctx.directory, tmp))
        raise _Exception('Deleting time_bnds failed for {0}'.format(file))


def _dates_from_filename(filename,calendar):
    """Returns datetime objetcs for start and end dates in filename."""
    pattern = re.compile(r'([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\d]+)-([\d]+).nc')
    dates=[]
    for i in [6, 7]:
        digits = _untroncated_timestamp(pattern.search(filename).group(i))
        # Convert string digits to %Y-%m-%d %H:%M:%S format
        date_as_since = ''.join([''.join(triple) for triple in zip(digits[::2],digits[1::2],['','-','-',' ',':',':',':'])])[:-1]
        # Use num2date to create netCDF4 datetime objects
        dates.append(num2date(0.0, units = 'days since '+ date_as_since, calendar = calendar))
    return dates


def _untroncated_timestamp(timestamp):
    """Returns proper digits for yearly and monthly truncated timestamp."""
    if len(timestamp) == 4:
        # Start year at january 1st
        return (timestamp+'0101').ljust(14,'0')
    elif len(timestamp) == 6:
        # Start month at first day
        return (timestamp+'01').ljust(14,'0')
    else:
        return timestamp.ljust(14,'0')


def _num2date(num_axis, units, calendar):
    """A wrapper from netCDF4.num2date able to handle 'years since' and 'months since' units"""
    # num_axis is the numerical time axis incremented following units (i.e., by years, months, days, etc).
    if not units.split(' ')[0] in ['years','months']:
        # If units are not 'years' or 'months since', call usual netcdftime.num2date:
        return num2date(num_axis, units = units, calendar = calendar)
    else:
        # Return to time refenence with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert the time refrence 'units_as_days' as datetime object
        start_date = num2date(0.0, units = units_as_days, calendar = calendar)
        # Control num_axis to always get an Numpy array (even with a scalar)
        num_axis_mod = np.atleast_1d(np.array(num_axis))
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering the whole 'num_axis' period
            max_years = np.floor(np.max(num_axis_mod)) + 1
            min_years = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([_add_year(start_date, years_to_add) for years_to_add in np.arange(min_years, max_years+2)])
            # Convert rebuilt years axis as 'number of days since'
            year_axis_as_days = date2num(years_axis, units = units_as_days, calendar = calendar)
            # Index of each years
            yind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' addint the number of days since referenced time with an half-increment (num_axis_mod - yind) = 0 or 0.5
            num_axis_mod_days = (year_axis_as_days[yind - int(min_years)] + (num_axis_mod - yind) * np.diff(year_axis_as_days)[yind - int(min_years)])
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering the whole 'num_axis' period
            max_months = np.floor(np.max(num_axis_mod)) + 1
            min_months = np.ceil(np.min(num_axis_mod)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([_add_month(start_date,months_to_add) for months_to_add in np.arange(min_months,max_months+12)])
            # Convert rebuilt months axis as 'number of days since'
            months_axis_as_days = date2num(months_axis, units = units_as_days, calendar = calendar)
            # Index of each months
            mind = np.vectorize(np.int)(np.floor(num_axis_mod))
            # Rebuilt num_axis as 'days since' addint the number of days since referenced time with an half-increment (num_axis_mod - mind) = 0 or 0.5
            num_axis_mod_days = (months_axis_as_days[mind - int(min_months)] + (num_axis_mod - mind) * np.diff(months_axis_as_days)[mind - int(min_months)])
        # Convert result as date axis
        return num2date(num_axis_mod_days, units = units_as_days, calendar = calendar)


def _date2num(date_axis, units, calendar):
    """A wrapper from netCDF4.date2num able to handle 'years since' and 'months since' units"""
    # date_axis is the date time axis incremented following units (i.e., by years, months, days, etc).
    if not units.split(' ')[0] in ['years','months']:
        # If units are not 'years' or 'months since', call usual netcdftime.date2num:
        return date2num(date_axis, units = units, calendar = calendar)
    else:
        # Return to time refenence with 'days since'
        units_as_days = 'days '+' '.join(units.split(' ')[1:])
        # Convert date axis as number of days since time reference
        days_axis = date2num(date_axis, units = units_as_days, calendar = calendar)
        # Convert the time refrence 'units_as_days' as datetime object
        start_date = num2date(0.0, units = units_as_days, calendar = calendar)
        # Create years axis from input date axis
        years = np.array([date.year for date in np.atleast_1d(np.array(date_axis))])
        if units.split(' ')[0] == 'years':
            # If units are 'years since'
            # Define the number of maximum and minimum years to build a date axis covering the whole 'num_axis' period
            max_years = np.max(years - start_date.year) + 1
            min_years = np.min(years - start_date.year) - 1
            # Create a date axis with one year that spans the entire period by year
            years_axis = np.array([_add_year(start_date,yid) for yid in np.arange(min_years, max_years+2)])
            # Convert years axis as number of days since time reference
            years_axis_as_days = date2num(years_axis, units = units_as_days, calendar = calendar)
            # Find closest index for years_axis_as_days in days_axis
            closest_index = np.searchsorted(years_axis_as_days, days_axis)
            # ???
            return min_years + closest_index + (days_axis - years_axis_as_days[closest_index]) / np.diff(years_axis_as_days)[closest_index]
        elif units.split(' ')[0] == 'months':
            # If units are 'months since'
            # Define the number of maximum and minimum months to build a date axis covering the whole 'num_axis' period
            max_months = np.max(12 * (years - start_date.year)) + 1
            min_months = np.min(12 * (years - start_date.year)) - 1
            # Create a date axis with one month that spans the entire period by month
            months_axis = np.array([_add_month(start_date,mid) for mid in np.arange(min_months,max_months+12)])
            # Convert months axis as number of days since time reference
            months_axis_as_days = date2num(months_axis, units = units_as_days, calendar = calendar)
            # Find closest index for months_axis_as_days in days_axis
            closest_index = np.searchsorted(months_axis_as_days, days_axis)
            # ???
            return min_months + closest_index + (days_axis - months_axis_as_days[closest_index]) / np.diff(months_axis_as_days)[closest_index]


def _add_month(date, months_to_add):
    """Finds the next month from date. Accepts datetime or phony datetime from netCDF4.num2date"""
    date_next = phony_datetime(year = date.year, month = date.month, day = date.day, hour = date.hour, minute = date.minute, second = date.second)
    years_to_add = int((date.month+months_to_add - np.mod(date.month+months_to_add - 1, 12) - 1) / 12)
    new_month = int(np.mod(date.month+months_to_add - 1, 12)) + 1
    date_next.year += years_to_add
    date_next.month = new_month
    return date_next


def _add_year(date, years_to_add):
    """Finds the next year from date. Accepts datetime or phony datetime from netCDF4.num2date"""
    date_next = phony_datetime(year = date.year, month = date.month, day = date.day, hour = date.hour, minute = date.minute, second = date.second)
    date_next.year += years_to_add
    return date_next


def _is_instant_time_axis(filename, realm):
   """Returns True if time time axis an instant axis."""
   need_instant_time = [('tas','3hr','atmos'),('uas','3hr','atmos'),('vas','3hr','atmos'),('huss','3hr','atmos'),('mrsos','3hr','land'),('tslsi','3hr','land'),('tso','3hr','ocean'),('ps','3hr','atmos'),('ua','6hrPlev','atmos'),('va','6hrPlev','atmos'),('ta','6hrPlev','atmos'),('psl','6hrPlev','atmos'),('ta','6hrLev','atmos'),('ua','6hrLev','atmos'),('va','6hrLev','atmos'),('hus','6hrLev','atmos'),('ps','6hrLev','atmos'),('clcalipso','cf3hr','atmos'),('clcalipso2','cf3hr','atmos'),('cfadDbze94','cf3hr','atmos'),('cfadLidarsr532','cf3hr','atmos'),('parasolRefl','cf3hr','atmos'),('cltcalipso','cf3hr','atmos'),('cllcalipso','cf3hr','atmos'),('clmcalipso','cf3hr','atmos'),('clhcalipso','cf3hr','atmos'),('cltc','cf3hr','atmos'),('zfull','cf3hr','atmos'),('zhalf','cf3hr','atmos'),('pfull','cf3hr','atmos'),('phalf','cf3hr','atmos'),('ta','cf3hr','atmos'),('h2o','cf3hr','atmos'),('clws','cf3hr','atmos'),('clis','cf3hr','atmos'),('clwc','cf3hr','atmos'),('clic','cf3hr','atmos'),('reffclws','cf3hr','atmos'),('reffclis','cf3hr','atmos'),('reffclwc','cf3hr','atmos'),('reffclic','cf3hr','atmos'),('grpllsprof','cf3hr','atmos'),('prcprof','cf3hr','atmos'),('prlsprof','cf3hr','atmos'),('prsnc','cf3hr','atmos'),('prlsns','cf3hr','atmos'),('reffgrpls','cf3hr','atmos'),('reffrainc','cf3hr','atmos'),('reffrains','cf3hr','atmos'),('reffsnowc','cf3hr','atmos'),('reffsnows','cf3hr','atmos'),('dtaus','cf3hr','atmos'),('dtauc','cf3hr','atmos'),('dems','cf3hr','atmos'),('demc','cf3hr','atmos'),('clc','cf3hr','atmos'),('cls','cf3hr','atmos'),('tas','cf3hr','atmos'),('ts','cf3hr','atmos'),('tasmin','cf3hr','atmos'),('tasmax','cf3hr','atmos'),('psl','cf3hr','atmos'),('ps','cf3hr','atmos'),('uas','cf3hr','atmos'),('vas','cf3hr','atmos'),('sfcWind','cf3hr','atmos'),('hurs','cf3hr','atmos'),('huss','cf3hr','atmos'),('pr','cf3hr','atmos'),('prsn','cf3hr','atmos'),('prc','cf3hr','atmos'),('evspsbl','cf3hr','atmos'),('sbl','cf3hr','atmos'),('tauu','cf3hr','atmos'),('tauv','cf3hr','atmos'),('hfls','cf3hr','atmos'),('hfss','cf3hr','atmos'),('rlds','cf3hr','atmos'),('rlus','cf3hr','atmos'),('rsds','cf3hr','atmos'),('rsus','cf3hr','atmos'),('rsdscs','cf3hr','atmos'),('rsuscs','cf3hr','atmos'),('rldscs','cf3hr','atmos'),('rsdt','cf3hr','atmos'),('rsut','cf3hr','atmos'),('rlut','cf3hr','atmos'),('rlutcs','cf3hr','atmos'),('rsutcs','cf3hr','atmos'),('prw','cf3hr','atmos'),('clt','cf3hr','atmos'),('clwvi','cf3hr','atmos'),('clivi','cf3hr','atmos'),('rtmt','cf3hr','atmos'),('ccb','cf3hr','atmos'),('cct','cf3hr','atmos'),('ci','cf3hr','atmos'),('sci','cf3hr','atmos'),('fco2antt','cf3hr','atmos'),('fco2fos','cf3hr','atmos'),('fco2nat','cf3hr','atmos'),('cl','cfSites','atmos'),('clw','cfSites','atmos'),('cli','cfSites','atmos'),('mc','cfSites','atmos'),('ta','cfSites','atmos'),('ua','cfSites','atmos'),('va','cfSites','atmos'),('hus','cfSites','atmos'),('hur','cfSites','atmos'),('wap','cfSites','atmos'),('zg','cfSites','atmos'),('rlu','cfSites','atmos'),('rsu','cfSites','atmos'),('rld','cfSites','atmos'),('rsd','cfSites','atmos'),('rlucs','cfSites','atmos'),('rsucs','cfSites','atmos'),('rldcs','cfSites','atmos'),('rsdcs','cfSites','atmos'),('tnt','cfSites','atmos'),('tnta','cfSites','atmos'),('tntmp','cfSites','atmos'),('tntscpbl','cfSites','atmos'),('tntr','cfSites','atmos'),('tntc','cfSites','atmos'),('tnhus','cfSites','atmos'),('tnhusa','cfSites','atmos'),('tnhusc','cfSites','atmos'),('tnhusd','cfSites','atmos'),('tnhusscpbl','cfSites','atmos'),('tnhusmp','cfSites','atmos'),('evu','cfSites','atmos'),('edt','cfSites','atmos'),('pfull','cfSites','atmos'),('phalf','cfSites','atmos'),('tas','cfSites','atmos'),('ts','cfSites','atmos'),('psl','cfSites','atmos'),('ps','cfSites','atmos'),('uas','cfSites','atmos'),('vas','cfSites','atmos'),('sfcWind','cfSites','atmos'),('hurs','cfSites','atmos'),('huss','cfSites','atmos'),('pr','cfSites','atmos'),('prsn','cfSites','atmos'),('prc','cfSites','atmos'),('evspsbl','cfSites','atmos'),('sbl','cfSites','atmos'),('tauu','cfSites','atmos'),('tauv','cfSites','atmos'),('hfls','cfSites','atmos'),('hfss','cfSites','atmos'),('rlds','cfSites','atmos'),('rlus','cfSites','atmos'),('rsds','cfSites','atmos'),('rsus','cfSites','atmos'),('rsdscs','cfSites','atmos'),('rsuscs','cfSites','atmos'),('rldscs','cfSites','atmos'),('rsdt','cfSites','atmos'),('rsut','cfSites','atmos'),('rlut','cfSites','atmos'),('rlutcs','cfSites','atmos'),('rsutcs','cfSites','atmos'),('prw','cfSites','atmos'),('clt','cfSites','atmos'),('clwvi','cfSites','atmos'),('clivi','cfSites','atmos'),('rtmt','cfSites','atmos'),('ccb','cfSites','atmos'),('cct','cfSites','atmos'),('ci','cfSites','atmos'),('sci','cfSites','atmos'),('fco2antt','cfSites','atmos'),('fco2fos','cfSites','atmos'),('fco2nat','cfSites','atmos')]
   pattern = re.compile(r'([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\d]+)-([\d]+).nc')
   if (pattern.search(filename).group(1), pattern.search(filename).group(2), realm) in need_instant_time:
      return True
   else:
      return False


def _time_inc(frequency):
    """Return tuple used for time incrementation depending on frequency: (raising value, time unit)."""
    inc = {'subhr': 30,
           '3hr'  : 3,
           '6hr'  : 6,
           'day'  : 1,
           'mon'  : 1,
           'yr'   : 1}
    return inc[frequency]


def _date_print(date):
    """Print date in format: %Y%m%d %H:%M:%s. Accepts datetime or phony datetime from netCDF4.num2date"""
    return '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(date.year, date.month, date.day, date.hour, date.minute, date.second)


def _rebuild_time_axis(start, length, instant, inc, ctx):
    """Rebuild time axis from date axis, depending on frequency and calendar."""
    date_axis, last = _rebuild_date_axis(start, length, instant, inc, ctx)
    axis = _date2num(date_axis, units = ctx.tunits, calendar = ctx.calendar)
    return axis, last


def _rebuild_date_axis(start, length, instant, inc, ctx):
    """Rebuild date axis from start date, depending on frequency and calendar."""
    num_axis = np.arange(start = start, stop = start + length * inc, step = inc)
    if ctx.funits.split(' ')[0] in ['years','months']:
        last = _num2date(num_axis[-1], units = ctx.funits, calendar = ctx.calendar)[0]
    else:
        last = _num2date(num_axis[-1], units = ctx.funits, calendar = ctx.calendar)
    if not instant:
        num_axis += 0.5 * inc
    date_axis = _num2date(num_axis, units = ctx.funits, calendar = ctx.calendar)
    return date_axis, last


def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])


def _time_checker(right_axis, test_axis):
   """Returns True if right axis is right."""
   if np.array_equal(right_axis, test_axis): return True
   else: return False


def _rebuild_time_bnds(start, length, inc, ctx):
    """Rebuild time boundaries from start date, depending on frequency and calendar."""
    num_axis_bnds = np.column_stack(((np.arange(start = start, stop  = start + length * inc, step  = inc)),
                                     (np.arange(start = start, stop  = start + (length+1) * inc, step  = inc)[1:])))
    date_axis_bnds = _num2date(num_axis_bnds, units = ctx.funits, calendar = ctx.calendar)
    axis_bnds = _date2num(date_axis_bnds, units = ctx.tunits, calendar = ctx.calendar)
    return axis_bnds


def _last_date_checker(last, end):
    """Returns True if last and end date are the same."""
    if last != end: return False
    else: return True


def main(ctx):
    """Main process."""
    # Set drving time properties (calendar, frequency and time units) from first file in directory
    _time_init(ctx)
    _log('info', 'Files to process = {0}'.format(len(glob('{0}/*.nc'.format(ctx.directory)))))
    # Process
    pool = ThreadPool(_THREAD_POOL_SIZE)
    outputs = pool.imap(_time_axis_processing, _get_file_list(ctx))
    # Returns pool and imap generator for different print depending the call
    return pool, outputs 


def run(job):
    """Main entry point for call by synda."""
    # Instanciate on processing context per file (for pool workers)
    ctx = _SyndaProcessingContext(job['full_path_variable'])
    if ctx.directory:
        _log('info', 'time_axis_normalization.py started (variable_path={0})'.format(ctx.directory))
        job['files'] = {}
        pool, outputs = main(ctx)
        for output in outputs:
            _log('info', '==> Filename:'.ljust(30)+'{0}'.format(output.file).rjust(70))
            if ctx.verbose:
                _log('info', '-> Start:'.ljust(30)+'{0}'.format(str(output.start)).rjust(70))
                _log('info', '-> End:'.ljust(30)+'{0}'.format(str(output.end)).rjust(70))
                _log('info', '-> Last:'.ljust(30)+'{0}'.format(str(output.last)).rjust(70))
            _log('info', '-> Timesteps:'.ljust(30)+'{0}'.format(output.steps).rjust(70))
            _log('info', '-> Instant time:'.ljust(30)+'{0}'.format(output.instant).rjust(70))
            _log('info', '-> Time axis status:'.ljust(30)+'{0}'.format(','.join(output.control)).rjust(70))
            _log('info', '-> Time boundaries:'.ljust(30)+'{0}'.format(output.bnds).rjust(70))
            _log('info', '-> New checksum:'.ljust(30)+'{0}'.format(output.checksum).rjust(70))
            if ctx.verbose:
                _log('info', '-> Time axis:')
                _log('info', '{0}'.format(fill(' | '.join(map(str, output.time.tolist())), width=100)))
                _log('info', '-> Theoretical axis:')
                _log('info', '{0}'.format(fill(' | '.join(map(str, output.axis.tolist())), width=100)))
            # Return diagnostic to synda using job dictionnary
            job['files'][output.file] = {}
            job['files'][output.file]['version'] = ctx.version
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
        _log('info', 'time_axis_normalization.py complete')
        return job


# Main entry point
if __name__ == "__main__":
    # Instanciate processing context per file (for pool workers)
    ctx = _ProcessingContext(_get_args())
    _log('info', 'Diagnostic started for {0}'.format(ctx.directory))
    pool, outputs = main(ctx)
    for output in outputs:
        _log('info', '==> Filename:'.ljust(30)+'{0}'.format(output.file).rjust(70))
        if ctx.verbose:
            _log('info', '-> Start:'.ljust(30)+'{0}'.format(str(output.start)).rjust(70))
            _log('info', '-> End:'.ljust(30)+'{0}'.format(str(output.end)).rjust(70))
            _log('info', '-> Last:'.ljust(30)+'{0}'.format(str(output.last)).rjust(70))
        _log('info', '-> Timesteps:'.ljust(30)+'{0}'.format(output.steps).rjust(70))
        _log('info', '-> Instant time:'.ljust(30)+'{0}'.format(output.instant).rjust(70))
        _log('info', '-> Time axis status:'.ljust(30)+'{0}'.format(','.join(output.control)).rjust(70))
        _log('info', '-> Time boundaries:'.ljust(30)+'{0}'.format(output.bnds).rjust(70))
        _log('info', '-> New checksum:'.ljust(30)+'{0}'.format(output.checksum).rjust(70))
        if ctx.verbose:
            _log('info', '-> Time axis:')
            _log('info', '{0}'.format(fill(' | '.join(map(str, output.time.tolist())), width=100)))
            _log('info', '-> Theoretical axis:')
            _log('info', '{0}'.format(fill(' | '.join(map(str, output.axis.tolist())), width=100)))
    # Close tread pool
    pool.close()
    pool.join() 
    _log('info', 'Diagnostic completed')
