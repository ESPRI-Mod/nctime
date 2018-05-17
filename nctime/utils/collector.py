#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect data from directories.

"""

import os
import re
import sys
from uuid import uuid4 as uuid

from nctime.utils.misc import match


class Collecting:
    """
    Spinner pending data collection.

    """
    STATES = ('/', '-', '\\', '|')
    step = 0

    def __init__(self, spinner):
        self.spinner = spinner
        self.next()

    def next(self):
        """
        Print collector spinner

        """
        if self.spinner:
            sys.stdout.write('\rCollecting data... {}'.format(Collecting.STATES[Collecting.step % 4]))
            sys.stdout.flush()
        Collecting.step += 1


class Collector(object):
    """
    Base collector class to yield regular NetCDF files.

    :param list sources: The list of sources to parse
    :param object data: Any object to attach to each collected data
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, sources, spinner=True):
        self.spinner = spinner
        self.sources = sources
        self.FileFilter = FilterCollection()
        self.PathFilter = FilterCollection()
        assert isinstance(self.sources, list)

    def __iter__(self):
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                if self.PathFilter(root):
                    for filename in sorted(filenames):
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield ffp

    def __len__(self):
        """
        Returns collector length with animation.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        progress = Collecting(self.spinner)
        s = 0
        for _ in self.__iter__():
            progress.next()
            s += 1
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
        return s

    def first(self):
        """
        Returns the first iterator element.

        """
        return self.__iter__().next()


class FilterCollection(object):
    """
    Regex dictionary with a call method to evaluate a string against several regular expressions.
    The dictionary values are 2-tuples with the regular expression as a string and a boolean
    indicating to match (i.e., include) or non-match (i.e., exclude) the corresponding expression.

    """
    FILTER_TYPES = (str, re._pattern_type)

    def __init__(self):
        self.filters = dict()

    def add(self, name=None, regex='*', inclusive=True):
        """Add new filter"""
        if not name:
            name = str(uuid())
        assert isinstance(regex, self.FILTER_TYPES)
        assert isinstance(inclusive, bool)
        self.filters[name] = (regex, inclusive)

    def __call__(self, string):
        return all([match(regex, string, inclusive=inclusive) for regex, inclusive in self.filters.values()])
