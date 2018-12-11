#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""
from multiprocessing import cpu_count, Lock
from multiprocessing.managers import SyncManager

from ESGConfigParser import SectionParser

from custom_exceptions import InvalidTable, InvalidFrequency
from nctime.utils.constants import *
from nctime.utils.custom_print import *
from nctime.utils.misc import get_project
from nctime.utils.time import TimeInit


class BaseContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        # Init print management
        Print.init(log=args.log, debug=args.debug, all=args.all, cmd=args.prog)
        # Print command-line
        Print.command()
        self._process_color_arg(args)
        # Get project and related configuration
        self.project = args.project
        self.config_dir = args.i
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        self.lock = Lock()
        self.nbfiles = 0
        self.nbskip = 0
        self.nberrors = 0
        self.file_filter = []
        if args.include_file:
            self.file_filter.extend([(f, True) for f in args.include_file])
        else:
            # Default includes netCDF only
            self.file_filter.append(('^.*\.nc$', True))
        if args.exclude_file:
            # Default exclude hidden files
            self.file_filter.extend([(f, False) for f in args.exclude_file])
        else:
            self.file_filter.append(('^\..*$', False))
        self.dir_filter = args.ignore_dir
        # Init process manager
        if self.use_pool:
            manager = SyncManager()
            manager.start()
            Print.BUFFER = manager.Value(c_char_p, '')
            self.progress = manager.Value('i', 0)
        else:
            self.progress = Value('i', 0)
        self.tunits_default = None
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        # Change frequency increment
        if args.set_inc:
            for table, frequency, increment, units in args.set_inc:
                if table not in set(zip(*FREQ_INC.keys())[0]):
                    raise InvalidTable(table)
                if frequency not in set(zip(*FREQ_INC.keys())[1]):
                    raise InvalidFrequency(frequency)
                keys = [(table, frequency)]
                if table == 'all':
                    keys = [k for k in FREQ_INC.keys() if k[1] == frequency]
                if frequency == 'all':
                    keys = [k for k in FREQ_INC.keys() if k[0] == table]
                for key in keys:
                    FREQ_INC[key] = [float(increment), str(units)]
        # Get reference time properties if submitted
        # Default is to deduce them from first file scanned
        self.ref_calendar = args.calendar
        self.ref_units = args.units
        # Init collector
        self.sources = None

    def __enter__(self):
        # Init file filter
        for regex, inclusive in self.file_filter:
            self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
        # Exclude fixed frequency in any case
        self.sources.FileFilter.add(regex='(_fx_|_fixed_|_fx.|_fixed.|_.fx_)', inclusive=False)
        # Init dir filter
        self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
        # Set driving time properties
        tinit = TimeInit(ref=self.sources.first(), tunits_default=self.tunits_default)
        if not self.ref_calendar:
            self.ref_calendar = tinit.calendar
        if not self.ref_units:
            self.ref_units = tinit.tunits
        # Get project id
        if not self.project:
            self.project = get_project(self.sources.first())
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Decline outputs depending on the scan results
        msg = COLORS.HEADER('Number of file(s) scanned: {}\n'.format(self.nbfiles))
        m = 'Number of file(s) skipped: {}'.format(self.nbskip)
        if self.nbskip:
            msg += COLORS.FAIL(m)
        else:
            msg += COLORS.SUCCESS(m)
        # Print summary
        Print.summary(msg)
        # Print log path if exists
        Print.log()

    def _process_color_arg(self, args):
        # process --color / --no-color arg if present
        if 'color' in args and args.color:
            enable_colors()
        if 'no_color' in args and args.no_color:
            disable_colors()
