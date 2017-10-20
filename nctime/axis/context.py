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
from nctime.utils.custom_exceptions import *
from nctime.utils.misc import cmd_exists
from nctime.utils.time import TimeInit


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args, directory):
        self.directory = directory
        self.config_dir = args.i
        self.write = args.write
        self.force = args.force
        self.verbose = args.v
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
        # Get checksum client
        self.checksum_client, self.checksum_type = self.get_checksum_client()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        # Init data collector
        self.sources = Collector(source=self.directory, data=self)
        # Init collector filter
        # Exclude hidden and/or non-NetCDF files
        self.sources.FileFilter['base_filter'] = ('^[!.].*\.nc$', True)
        # Exclude fixed frequency
        self.sources.FileFilter['frequency_filter'] = ('(_fx_|_fixed_|_fx.|_fixed.)', True)
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
            logging.info('Time diagnostic completed ({} files scanned)'.format(self.scan_files))
            sys.exit(0)

    def get_checksum_client(self):
        """
        Gets the checksum client to use.
        Be careful to Exception constants by reading two different sections.

        :returns: The checksum client
        :rtype: *str*

        """
        _cfg = SectionParser(section='DEFAULT', directory=self.config_dir)
        if _cfg.has_option('DEFAULT', 'checksum'):
            checksum_client, checksum_type = _cfg.get_options_from_table('checksum')[0]
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            checksum_client, checksum_type = 'sha256sum', 'SHA256'
        if not cmd_exists(checksum_client):
            raise ChecksumClientNotFound(checksum_client)
        else:
            return checksum_client, checksum_type
