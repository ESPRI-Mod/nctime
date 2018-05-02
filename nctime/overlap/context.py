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

from handler import Graph
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
        self.resolve = args.resolve
        self.full_overlap_only = args.full_overlap_only
        self.project = args.project
        self.tunits_default = None
        self.threads = args.max_threads
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.overlaps = False
        self.broken = False
        self.scan_files = None
        self.pbar = None

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        # Init data collector
        self.sources = Collector(sources=self.directory, data=self)
        # Init collector filter
        # Exclude hidden non-NetCDF files
        self.sources.FileFilter.add(regex='^.*\.nc$')
        # Exclude fixed frequency
        self.sources.FileFilter.add(regex='(_fx_|_fixed_|_fx.|_fixed.|_.fx_)', inclusive=False)
        # Get first file for reference
        self.ref = self.sources.first()[0]
        self.display = len(os.path.basename(self.ref))
        # Set driving time properties
        self.tinit = TimeInit(ref=self.ref, tunits_default=self.tunits_default)
        # DiGraph creation
        self.graph = Graph()
        # Init threads pool
        self.pool = ThreadPool(int(self.threads))
        return self

    def __exit__(self, *exc):
        # Close tread pool
        self.pool.close()
        self.pool.join()
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
