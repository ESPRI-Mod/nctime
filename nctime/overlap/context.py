#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""
import logging
import os
import sys

import networkx as nx
from ESGConfigParser import SectionParser

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
        self.resolve = args.resolve
        self.full_overlap_only = args.full_overlap_only
        self.verbose = args.v
        self.project = args.project
        self.tunits_default = None
        if self.project in DEFAULT_TIME_UNITS.keys():
            self.tunits_default = DEFAULT_TIME_UNITS[self.project]
        self.path = []
        self.full_overlaps = None
        self.partial_overlaps = None
        self.broken = False

    def __enter__(self):
        # Get checksum client
        self.checksum_client, self.checksum_type = self.get_checksum_client()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.pattern = self.cfg.translate('filename_format')
        # Init data collector
        self.sources = Collector(source=self.directory)
        # Init collector filter
        # Exclude hidden non-NetCDF files
        self.sources.FileFilter['base_filter'] = ('^[!.].*\.nc$', True)
        # Exclude fixed frequency
        self.sources.FileFilter['frequency_filter'] = ('(_fx_|_fixed_|_fx.|_fixed.)', True)
        # Get first file for reference
        self.ref = self.sources.first()
        self.display = len(os.path.basename(self.ref))
        # Set driving time properties
        self.tinit = TimeInit(ref=self.ref, tunits_default=self.tunits_default)
        # DiGraph creation
        self.graph = nx.DiGraph()
        return self

    def __exit__(self, *exc):
        # Decline outputs depending on the scan results
        # Default is sys.exit(0)
        # Print first node
        m = ' START '.center(self.display + 2, '-')
        msg = '\n                                   {}'.format(m)
        # Print intermediate nodes
        for i in range(1, len(self.path) - 2):
            m = ' {} '.format(self.path[i]).center(self.display + 2, '~')
            if self.partial_overlaps and self.path[i] in self.partial_overlaps:
                m = ' {} < overlap from {} to {} '.format(self.path[i].center(self.display + 2),
                                                          self.partial_overlaps[self.path[i]]['start_date'],
                                                          self.partial_overlaps[self.path[i]]['end_overlap'])
            msg += '\n                                   {}'.format(m)
        # Print last node
        m = ' END '.center(self.display + 2, '-')
        msg += '\n                                   {}'.format(m)
        # Print analyse result
        if self.broken:
            logging.error('Time series broken: {}'.format(msg))
            sys.exit(1)
        else:
            logging.info('Shortest path found: {}'.format(msg))
        # Print overlaps if exists
        if not self.full_overlaps and not self.partial_overlaps:
            logging.info('No overlapping files')
        else:
            logging.warning('Overlapping files:')
            for node in self.full_overlaps:
                if self.resolve:
                    logging.warning('{} > REMOVED'.format(node))
                else:
                    logging.warning('{} > TO REMOVE'.format(node))
            for node in self.partial_overlaps:
                if self.resolve and not self.full_overlap_only:
                    logging.warning('{} > TRUNCATED'.format(node))
                else:
                    logging.warning('{} > TO TRUNCATE'.format(node))
        # End
        logging.info('Overlap diagnostic completed')

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
