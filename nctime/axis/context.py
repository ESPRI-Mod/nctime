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
from nctime.utils.custom_exceptions import NoRunCardFound
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
        self.input = args.input
        self.write = args.write
        self.force = args.force
        self.debug = args.debug
        self.on_fly = args.on_fly
        if args.card:
            self.on_fly = True if not is_simulation_completed(args.card) else False
        self.limit = args.limit
        self.ignore_codes = args.ignore_errors
        self.correction = args.correct_timestamp
        self.status = []
        self.file_filter = []

    def __enter__(self):
        # Print warning message if on-fly mode
        if self.on_fly:
            Print.warning('"on-fly" mode activated -- Incomplete time axis expected')
        # Init data collector
        self.sources = Collector(sources=self.input, spinner=False)
        # Run __enter__() BaseContext
        super(self.__class__, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        m = 'Number of file with error(s): {}'.format(self.nberrors)
        if self.nberrors:
            msg = COLORS.FAIL(m)
        else:
            msg = COLORS.SUCCESS(m)
        Print.summary(msg)
        # Run __exit__() BaseContext
        super(self.__class__, self).__exit__(exc_type, exc_val, traceback)


def is_simulation_completed(card_path):
    """
    Returns True if the simulation is completed.

    :param str card_path: Directory including run.card
    :returns: True if the simulation is completed
    :rtype: *boolean*

    """
    # Check cards exist
    if RUN_CARD not in os.listdir(card_path):
        raise NoRunCardFound(card_path)
    else:
        run_card = os.path.join(card_path, RUN_CARD)
    # Extract info from cards
    config = SectionParser('Configuration')
    config.read(run_card)
    return config.get('periodstate').strip('"') == 'Completed'
