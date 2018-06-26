#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from ESGConfigParser import SectionParser

from nctime.utils.collector import Collector
from nctime.utils.constants import *
from nctime.utils.context import BaseContext
from nctime.utils.custom_exceptions import NoConfigCardFound, NoRunCardFound
from nctime.utils.custom_print import *


class ProcessingContext(BaseContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(self.__class__, self).__init__(args)
        self.directory = args.directory
        self.resolve = args.resolve
        self.full_only = args.full_only
        self.overlaps = 0
        self.broken = 0
        self.card = args.card
        if args.card:
            self.card = list(yield_xml_from_card(args.card))
        self.nbnodes = 0
        self.nbdsets = 0

    def __enter__(self):
        # Init data collector
        self.sources = Collector(sources=self.directory)
        # Run __enter__() BaseContext
        super(self.__class__, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        msg = COLORS.OKBLUE('Number of node(s): {}\n'.format(self.nbnodes))
        msg += COLORS.HEADER('Number of dataset(s): {}\n'.format(self.nbdsets))
        m = 'Number of datasets with overlap(s): {}\n'.format(self.overlaps)
        if self.overlaps:
            msg += COLORS.FAIL(m)
        else:
            msg += COLORS.SUCCESS(m)
        m = 'Number of datasets with broken time series: {}'.format(self.broken)
        if self.broken:
            msg += COLORS.FAIL(m)
        else:
            msg += COLORS.SUCCESS(m)
        Print.summary(msg)
        # Run __exit__() BaseContext
        super(self.__class__, self).__exit__(exc_type, exc_val, traceback)


def yield_xml_from_card(card_path):
    """
    Yields XML path from run.card and config.card attributes.

    :param str card_path: Directory including run.card and config.card
    :returns: The XML paths to use
    :rtype: *iter*

    """
    # Check cards exist
    if RUN_CARD not in os.listdir(card_path):
        raise NoRunCardFound(card_path)
    else:
        run_card = os.path.join(card_path, RUN_CARD)
    if CONF_CARD not in os.listdir(card_path):
        raise NoConfigCardFound(card_path)
    else:
        conf_card = os.path.join(card_path, CONF_CARD)
    # Extract config info from config.card
    config = SectionParser('UserChoices')
    config.read(conf_card)
    xml_attrs = dict()
    xml_attrs['root'] = FILEDEF_ROOT
    xml_attrs['longname'] = config.get('longname').strip('"')
    xml_attrs['experimentname'] = config.get('experimentname').strip('"')
    if config.has_option('modelname'):
        xml_attrs['modelname'] = config.get('modelname').strip('"')
    else:
        xml_attrs['modelname'] = 'IPSL-CM6A-LR'
    xml_attrs['member'] = config.get('member').strip('"')
    # Extract first and last simulated years from run.card
    with open(run_card, 'r') as f:
        lines = f.read().split('\n')
    # Get run table without header
    lines = [line for line in lines if line.count('|') == 8][1:]
    year_start = int(lines[0].split()[3][:4])
    year_end = int(lines[-1].split()[5][:4])
    for year in range(year_start, year_end + 1):
        xml_attrs['year'] = str(year)
        yield FILEDEF_DIRECTORY_FORMAT.format(**xml_attrs)
