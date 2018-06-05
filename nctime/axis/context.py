#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
from multiprocessing import cpu_count
from time import sleep

from ESGConfigParser import SectionParser

from nctime.utils.collector import Collector
from nctime.utils.constants import *
from nctime.utils.custom_exceptions import InvalidFrequency
from nctime.utils.misc import COLORS, get_project
from nctime.utils.time import TimeInit


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.input = args.input
        self.config_dir = args.i
        self.write = args.write
        self.force = args.force
        self.debug = args.debug
        self.on_fly = args.on_fly
        self.limit = args.limit
        self.ignore_codes = args.ignore_errors
        self.project = args.project
        if args.set_inc:
            for frequency, increment in dict(args.set_inc).items():
                if frequency not in FREQ_INC.keys():
                    raise InvalidFrequency(frequency)
                FREQ_INC[frequency][0] = int(increment)
        self.tunits_default = None
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        self.scan_files = 0
        self.scan_errors = 0
        self.correction = args.correct_timestamp
        self.status = []
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

    def __enter__(self):
        # Init data collector
        self.sources = Collector(sources=self.input, spinner=False)
        # Init file filter
        for regex, inclusive in self.file_filter:
            self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
        # Exclude fixed frequency in any case
        self.sources.FileFilter.add(regex='(_fx_|_fixed_|_fx.|_fixed.|_.fx_)', inclusive=False)
        # Init dir filter
        self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
        # Set driving time properties
        self.tinit = TimeInit(ref=self.sources.first(), tunits_default=self.tunits_default)
        self.ref_calendar = self.tinit.calendar
        self.ref_units = self.tinit.tunits
        # Get project id
        if not self.project:
            self.project = get_project(self.sources.first())
        # Get default time units if exists (i.e., CORDEX case)
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Sleep time before final print
        sleep(0.1)
        # Decline outputs depending on the scan results
        msg = COLORS.HEADER + '\nNumber of files scanned: {}\n'.format(self.scan_files) + COLORS.ENDC
        if self.scan_errors:
            msg += COLORS.FAIL
        else:
            msg += COLORS.OKGREEN
        msg += 'Number of file with error(s): {}'.format(self.scan_errors) + COLORS.ENDC
        # Critical level used to print in any case
        logging.critical(msg)
        # Print log path if exists
        log_handler = logging.getLogger().handlers[0]
        if hasattr(log_handler, 'baseFilename') and os.path.exists(log_handler.baseFilename):
            print(COLORS.HEADER + '\nSee log: {}'.format(log_handler.baseFilename) + COLORS.ENDC)
