#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool

from ESGConfigParser import SectionParser

from constants import *
from nctime.utils.collector import Collector
from nctime.utils.constants import *
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
        self.write = args.write
        self.force = args.force
        self.debug = args.debug
        self.project = args.project
        self.tunits_default = None
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.threads = args.max_threads
        self.db = None
        if args.db:
            self.db = os.path.realpath(args.db)
        self.scan_files = None
        self.status = []

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        # Init data collector
        self.sources = Collector(sources=self.directory, spinner=False, data=self)
        # Init collector filter
        # Exclude hidden and/or non-NetCDF files
        self.sources.FileFilter.add(regex='^.*\.nc$')
        # Exclude fixed frequency
        self.sources.FileFilter.add(regex='(_fx_|_fixed_|_fx.|_fixed.|_.fx_)', inclusive=False)
        # Set driving time properties
        self.tinit = TimeInit(ref=self.sources.first()[0], tunits_default=self.tunits_default)
        # Init threads pool
        self.pool = ThreadPool(int(self.threads))
        return self

    def __exit__(self, *exc):
        # Close tread pool
        self.pool.close()
        self.pool.join()
        # Decline outputs depending on the scan results
        # Default is sys.exit(0)
        if any([s in EXIT_ERRORS for s in self.status]):
            logging.error('Some time axis should be corrected manually ({} files scanned)'.format(self.scan_files))
            sys.exit(1)
        else:
            print('All time axis seem correct ({} files scanned)'.format(self.scan_files))
            sys.exit(0)
