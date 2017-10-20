#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect data from directories.

"""

import os

from nctime.utils.misc import match


class Collector(object):
    """
    Base collector class to yield regular NetCDF files.

    :param str source: The list of sources to parse
    :param object data: Any object to attach to each collected data
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, source, data=None):
        self.source = source
        self.data = data
        self.FileFilter = Filter()
        assert os.path.isdir(self.source)

    def __iter__(self):
        for root, _, filenames in os.walk(self.source, followlinks=True):
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

        :return:
        """
        return self.__iter__().next()


class Filter(dict):
    """
    Regex dictionary with a call method to evaluate a string against several regular expressions.
    The dictionary values are 2-tuples with the regular expression as a string and a boolean
    indicating to match (i.e., include) or non-match (i.e., exclude) the corresponding expression.

    """

    def __setitem__(self, key, value):
        # Assertions on filters values
        if isinstance(value, tuple):
            assert len(value) == 2
            assert isinstance(value[0], str)
            assert isinstance(value[1], bool)
        else:
            assert isinstance(value, str)
            # Set negative = False by default
            value = (value, False)
        dict.__setitem__(self, key, value)

    def __call__(self, string):
        return all([match(regex, string, negative=negative) for regex, negative in self.values()])
