#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""
import logging
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
        self.directory = args.directory
        self.config_dir = args.i
        self.resolve = args.resolve
        self.full_overlap_only = args.full_overlap_only
        self.project = args.project
        if args.set_inc:
            for frequency, increment in dict(args.set_inc).items():
                if frequency not in FREQ_INC.keys():
                    raise InvalidFrequency(frequency)
                FREQ_INC[frequency][0] = int(increment)
        self.tunits_default = None
        self.processes = args.max_processes
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.overlaps = False
        self.broken = False
        self.scan_files = None
        self.pbar = None
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
        self.sources = Collector(sources=self.directory)
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
        # Default is sys.exit(0)
        # Print analyse result
        if self.broken:
            logging.error('Some broken time period should be '
                          'corrected manually ({} files scanned)'.format(self.scan_files))
            sys.exit(1)
        elif self.overlaps:
            logging.error('Some time period have overlaps to'
                          ' fix ({} files scanned)'.format(self.scan_files))
            sys.exit(2)
        else:
            print('No overlaps or broken time periods '
                  '({} files scanned)'.format(self.scan_files))
            sys.exit(0)
