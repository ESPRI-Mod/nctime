#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Highlight chunked NetCDF files producing overlap in a time series.

"""

import logging
import os
import re
import sys

import networkx as nx

from nctime.utils import time, utils


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +-----------------------+-------------+---------------------------------+
    | Attribute             | Type        | Description                     |
    +=======================+=============+=================================+
    | *self*.directory      | *str*       | Variable to scan                |
    +-----------------------+-------------+---------------------------------+
    | *self*.mip            | *str*       | The MIP table from DRS          |
    +-----------------------+-------------+---------------------------------+
    | *self*.remove         | *boolean*   | True if remove mode             |
    +-----------------------+-------------+---------------------------------+
    | *self*.verbose        | *boolean*   | True if verbose mode            |
    +-----------------------+-------------+---------------------------------+
    | *self*.subtree        | *boolean*   | True for sub-period use         |
    +-----------------------+-------------+---------------------------------+
    | *self*.project        | *str*       | MIP project                     |
    +-----------------------+-------------+---------------------------------+
    | *self*.pattern        | *re object* | Filename regex pattern          |
    +-----------------------+-------------+---------------------------------+
    | *self*.tunits_default | *str*       | Default time units              |
    +-----------------------+-------------+---------------------------------+
    | *self*.ref            | *str*       | First filename as reference     |
    +-----------------------+-------------+---------------------------------+
    | *self*.variable       | *str*       | MIP variable                    |
    +-----------------------+-------------+---------------------------------+

    :param *ArgumentParser* args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.directory = args.directory
        self.mip = args.mip
        self.remove = args.remove
        self.verbose = args.v
        self.subtree = args.subtree
        self.project = args.project
        cfg = utils.config_parse(args.i, self.project)
        self.pattern = utils.translate_filename_format(cfg, self.project)
        if cfg.has_option('time_units_default', self.project):
            self.tunits_default = cfg.get(self.project, 'time_units_default')
        else:
            self.tunits_default = None
        self.ref = self.get_files_list().next()
        self.variable = unicode(self.ref.split('_')[0])

    def get_files_list(self):
        """
        Yields all files into a directory.

        :returns: A file iterator
        :rtype: *iter*

        """
        for filename in sorted(os.listdir(self.directory)):
            if not os.path.isfile(os.path.join(self.directory, filename)):
                logging.warning('{0} is not a file and was skipped'.format(filename))
                continue
            if any(test_fx in filename for test_fx in ['_fx_', '_fixed_', '_fx.', '_fixed.']):
                logging.warning('STOP because "fixed" frequency has no time axis')
                sys.exit(0)
            if not re.match(self.pattern, filename):
                logging.warning('{0} has invalid filename and was skipped'.format(filename))
                continue
            yield filename


def get_overlaps(nodes, shortest, overlaps=True):
    """
    Yields all matching or overlapping (default) files.

    :param list nodes: The directed graph nodes as a list of tuples
    :param list shortest: The most consecutive files list (from `nx.DiGraph()`)
    :param boolean overlaps: True if overlaps are returned
    :returns: The filenames
    :rtype: *list*

    """
    match = []
    for i in range(len(shortest) - 1):
        match.append(zip(*nodes)[0][zip(*nodes)[1].index(shortest[i]) and
                                    zip(*nodes)[3].index(shortest[i + 1])])
    # Find overlapping filenames
    if overlaps:
        return list(set(zip(*nodes)[0]).symmetric_difference(set(match)))
    else:
        return match


def main(args):
    """
    Main process that\:
     * Instanciates processing context,
     * Deduces start, end and next date from each filenames,
     * Builds the DiGraph,
     * Detects the shortest path between dates if exists,
     * Removes the overlapping files.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionnary
    ctx = ProcessingContext(args)
    logging.info('Overlap diagnostic started for {0}'.format(ctx.directory))
    # Set driving time properties (e.g., calendar, frequency and time units) from first file in directory
    tinit = time.TimeInit(ctx)
    # DiGraph creation
    graph = nx.DiGraph()
    graph.clear()
    nodes = []
    if ctx.verbose:
        logging.info('{0} | {1} | {2} | {3}'.format('File'.center(len(ctx.ref) + 2),
                                                    'Start'.center(19),
                                                    'End'.center(19),
                                                    'Next'.center(19)))
    for filename in ctx.get_files_list():
        start, end, nxt = time.get_start_end_dates_from_filename(filename=filename,
                                                                 pattern=ctx.pattern,
                                                                 frequency=tinit.frequency,
                                                                 calendar=tinit.calendar)
        if ctx.verbose:
            logging.info('{0} | {1} | {2} | {3}'.format(filename.center(len(filename) + 2),
                                                        time.date2str(start).center(19),
                                                        time.date2str(end).center(19),
                                                        time.date2str(nxt).center(19)))
        # A node is defined by its start, end and next dates as a tuple.
        start, end, nxt = time.dates2str([start, end, nxt], sep=False)
        nodes.append((filename, int(start), int(end), int(nxt)))
        # Add nodes and edges
        graph.add_edge(int(start), int(nxt))
    # Walk through the graph
    try:
        # Find shortest path between oldest and latest dates
        shortest = nx.shortest_path(graph,
                                    source=min(zip(*nodes)[1]),
                                    target=max(zip(*nodes)[3]))
        logging.info('Shortest path found')
        overlaps = get_overlaps(nodes, shortest, overlaps=True)
    except nx.NetworkXNoPath, e:
        if ctx.subtree:
            # Find shortest path of the subtree instead
            pred, dist = nx.bellman_ford(graph, min(zip(*nodes)[1]))
            latest = utils.find_key(dist, max(dist.values()))
            shortest = nx.shortest_path(graph,
                                        source=min(zip(*nodes)[1]),
                                        target=latest)
            logging.warning('Shortest path found on the longest subtree from start:')
            for filename in get_overlaps(nodes, shortest, overlaps=False):
                logging.warning(filename)
            overlaps = get_overlaps(nodes, shortest, overlaps=True)
        else:
            logging.warning('No shortest path found: {0}'.format(str(e)))
            overlaps = None
    # Print results
    if not overlaps:
        logging.info('No overlapping files')
    else:
        logging.warning('Overlapping files:')
        for filename in overlaps:
            logging.warning(filename)
    if ctx.remove:
        for filename in overlaps:
            os.remove('{0}/{1}'.format(ctx.directory, filename))
        logging.warning('{0} overlapping files removed'.format(len(overlaps)))
    logging.info('Overlap diagnostic completed')
