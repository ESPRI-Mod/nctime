#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect data from directories.

"""

import os
import re
from uuid import uuid4 as uuid
from nctime.utils.misc import match


class Collector(object):
    """
    Base collector class to yield regular NetCDF files.

    :param list sources: The list of sources to parse
    :param object data: Any object to attach to each collected data
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, source, data=None):
        self.source = source
        self.data = data
        self.FileFilter = FilterCollection()
        self.PathFilter = FilterCollection()
        assert os.path.isdir(self.source), 'No such directory: {}'.format(self.source)

    def __iter__(self):
        for root, _, filenames in os.walk(source, followlinks=True):
            if self.PathFilter(root):
                for filename in sorted(filenames):
                    ffp = os.path.join(root, filename)
                    if os.path.isfile(ffp) and self.FileFilter(filename):
                        yield self.attach(ffp)

    def __len__(self):
        """
        Returns collector length.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        s = 0
        for _ in self.__iter__():
            s += 1
        return s

    def attach(self, item):
        """
        Attach any object to the each collector item.

        :param str item: The collector item
        :returns: The collector item with the "data" object
        :rtype: *tuple*

        """
        return (item, self.data) if self.data else item

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
