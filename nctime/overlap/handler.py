#!/usr/bin/env python
"""
.. module:: nctime.axis.handler.py
   :platform: Unix
   :synopsis: File handler for time axis.

"""

import logging
import os
from copy import deepcopy as copy

import networkx as nx
from fuzzywuzzy import fuzz, process

from nctime.utils.constants import CLIM_SUFFIX
from nctime.utils.custom_exceptions import *
from nctime.utils.misc import ncopen
from nctime.utils.time import get_start_end_dates_from_filename, \
    get_first_last_timesteps, dates2int


class Filename(object):
    """
    Handler providing methods to deal with file processing.

    """

    def __init__(self, ffp):
        self.ffp = ffp
        # Retrieve filename
        self.filename = os.path.basename(ffp)
        # Remove "-clim.nc" suffix from filename if exists
        self.name = self.filename.replace(CLIM_SUFFIX, '.nc') if self.filename.endswith(CLIM_SUFFIX) else self.filename
        # Build id as the filename without the dates and extension
        self.id = '_'.join(self.filename.split('_')[:-1])
        # Get first and last time steps
        self.first_timestep, self.last_timestep = get_first_last_timesteps(ffp)
        # Start/end period dates from filename + next expected date
        self.start_date = None
        self.end_date = None
        self.next_date = None

    def get_start_end_dates(self, pattern, calendar):
        """
        Wraps and records :func:`get_start_end_dates_from_filename` results.

        :param re Object pattern: The filename pattern as a regex (from `re library \
        <https://docs.python.org/2/library/re.html>`_).
        :param str calendar: The NetCDF calendar attribute
        :returns: Start and end dates as number of days since the referenced date
        :rtype: *float*

        """
        # Get frequency
        frequency = None
        with ncopen(self.ffp) as nc:
            # Get frequency from file
            if 'frequency' in nc.ncattrs():
                frequency = nc.getncattr('frequency')
            else:
                key, score = process.extractOne('frequency', nc.ncattrs(), scorer=fuzz.partial_ratio)
                if score >= 80:
                    frequency = nc.getncattr(key)
                    logging.warning('Consider "{}" attribute instead of "frequency"'.format(key))
                else:
                    raise NoNetCDFAttribute('frequency', self.ffp)
        dates = get_start_end_dates_from_filename(filename=self.name,
                                                  pattern=pattern,
                                                  frequency=frequency,
                                                  calendar=calendar)
        self.start_date, self.end_date, self.next_date = dates2int(dates)


class Graph(object):
    """
    Handler providing methods to deal with Directed graph.

    """

    def __init__(self):
        pass

    def has_graph(self, i):
        return True if hasattr(self, i) else False

    def set_graph(self, i, g=nx.DiGraph()):
        setattr(self, i, copy(g))

    def get_graph(self, i):
        return copy(getattr(self, i))

    def __call__(self, *args, **kwargs):
        return [id for id in self.__dict__]
