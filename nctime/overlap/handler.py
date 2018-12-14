#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: File handler for time axis.

"""

from copy import deepcopy as copy

from fuzzywuzzy import fuzz, process
from networkx import DiGraph

from nctime.utils.constants import CLIM_SUFFIX
from nctime.utils.custom_exceptions import *
from nctime.utils.custom_print import *
from nctime.utils.misc import ncopen
from nctime.utils.time import get_start_end_dates_from_filename, dates2int


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
        if self.filename.endswith(CLIM_SUFFIX):
            self.id = '_'.join(self.filename.split('_')[:-1]) + '-clim'
        else:
            self.id = '_'.join(self.filename.split('_')[:-1])
        # Get first and last time steps
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
        # Get table from file
        try:
            table = self.nc_att_get('table_id')
            # Extract MIP table from string if needed
            table = table.split(" ")[1]
        except IndexError:
            table = self.nc_att_get('table_id')
        except NoNetCDFAttribute:
            table = 'None'
        # Rollback to None if unknown table
        if table not in set(zip(*FREQ_INC.keys())[0]):
            msg = 'Unknown MIP table "{}" -- Consider default increment for the given frequency.'.format(table)
            Print.warning(msg, buffer=True)
            table = 'None'
        # Get frequency from file
        frequency = self.nc_att_get('frequency')
        dates = get_start_end_dates_from_filename(filename=self.name,
                                                  pattern=pattern,
                                                  table=table,
                                                  frequency=frequency,
                                                  calendar=calendar)
        self.start_date, self.end_date, self.next_date = dates2int(dates)

    def nc_att_get(self, attribute, variable=None):
        """
        Get attribute from NetCDF file. Default is to find into global attributes.
        If attribute key is not found, get the closest key name instead.


        :param str attribute: The attribute key to get
        :param str variable: The variable from which to find the attribute. Global is None.
        :return: The attribute value
        :rtype: *str*

        """
        with ncopen(self.ffp) as nc:
            if variable:
                attrs = nc.variables[variable].__dict__
            else:
                attrs = nc.__dict__
            if attribute in attrs.keys():
                return attrs[attribute]
            else:
                try:
                    key, score = process.extractOne(attribute, attrs, scorer=fuzz.partial_ratio)
                    if score >= 80:
                        Print.warning('Consider "{}" attribute instead of "frequency"'.format(key))
                        return attrs(key)
                    else:
                        raise NoNetCDFAttribute(attribute, self.ffp)
                except:
                    raise NoNetCDFAttribute(attribute, self.ffp)

class Graph(object):
    """
    Handler providing methods to deal with Directed graph.

    """

    def __init__(self):
        pass

    def has_graph(self, i):
        return True if hasattr(self, i) else False

    def set_graph(self, i, g=DiGraph()):
        setattr(self, i, copy(g))

    def get_graph(self, i):
        return copy(getattr(self, i))

    def add_node(self, i, filename, start=None, end=None, next=None, path=None):
        g = getattr(self, i)
        g.add_node(filename,
                   start=start,
                   end=end,
                   next=next,
                   path=path)
        return g.node[filename]

    def add_edge(self, i, node_src, node_dst):
        g = getattr(self, i)
        g.add_edge(node_src, node_dst)

    def __call__(self, *args, **kwargs):
        return [id for id in self.__dict__]
