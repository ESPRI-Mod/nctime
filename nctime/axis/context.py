#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import sys

from ESGConfigParser import SectionParser

from nctime.utils.collector import Collector
from nctime.utils.constants import *
from nctime.utils.custom_exceptions import InvalidFrequency
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
        self.project = args.project
        if args.set_inc:
            for frequency, increment in dict(args.set_inc).items():
                if frequency not in FREQ_INC.keys():
                    raise InvalidFrequency(frequency)
                FREQ_INC[frequency][0] = int(increment)
        self.tunits_default = None
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.processes = args.max_processes
        self.use_pool = (self.processes != 1)
        self.scan_files = 0
        self.scan_errors = 0
        self.true_dates = args.true_dates
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
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
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
        return self

    def __exit__(self, *exc):
        # Decline outputs depending on the scan results
        print('Number of files scanned: {}'.format(self.scan_files))
        print('Number of file with error(s): {}'.format(self.scan_errors))
        if self.scan_errors:
            sys.exit(1)
        else:
            sys.exit(0)
