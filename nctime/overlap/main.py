#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Highlight chunked NetCDF files producing overlap in a time series.

"""

import itertools
import logging
import os
import re
from multiprocessing import Pool
from multiprocessing.managers import BaseManager

import nco
import networkx as nx
import numpy as np

from context import ProcessingContext
from handler import Filename, Graph
from nctime.utils.time import get_next_timestep


def get_overlaps(g, shortest):
    """
    Returns all overlapping files (default) as a list of tuples. Each tuple gathers\:
     * The higher overlap bound,
     * The date to cut the file in order to resolve the overlap,
     * The corresponding cutting timestep.

    :param str directory: The directory scanned
    :param networkx.DiGraph() g: The directed graph
    :param list shortest: The most consecutive files list (from `nx.DiGraph().shortest_path`)
    :returns: The filenames
    :rtype: *list*

    """
    overlaps = dict()
    # Find partial overlapping nodes
    overlaps['partial'] = dict()
    for n in range(1, len(shortest) - 2):
        # Get current node dates
        current_node = g.node[shortest[n]]
        # Get next node dates
        next_node = g.node[shortest[n + 1]]
        # Because of the shortest path is selected, difference between bounds should always be positive or zero
        assert (current_node['next'] - next_node['start']) >= 0
        # Get partial overlap if exists
        # Partial overlap from next_node[1] to current_node[2] (bounds included)
        # Overlap is hold on the next node (arbitrary)
        if (current_node['next'] - next_node['start']) > 0:
            logging.debug('Partial overlap found between {} and {}'.format(current_node, next_node))
            cutting_timestep = get_next_timestep(next_node['path'], current_node['last_step'])
            overlaps['partial'][shortest[n + 1]] = next_node
            overlaps['partial'][shortest[n + 1]].update({'end_overlap': current_node['end'],
                                                         'cutting_date': current_node['next'],
                                                         'cutting_timestep': cutting_timestep})
    # Find full overlapping nodes
    overlaps['full'] = list(set(g.nodes()).symmetric_difference(set(shortest)))
    return overlaps['partial'], overlaps['full']


def resolve_overlap(directory, pattern, filename, from_date=None, to_date=None, cutting_timestep=None, partial=False):
    """
    Resolve overlapping files.
    If full overlap, the corresponding file is removed.
    If partial overlap, the corresponding file is truncated into a new one and the old file is removed.

    :param str directory: The directory scanned
    :param str pattern: The filename pattern
    :param str filename: The filename
    :param int from_date: Overlap starting date
    :param int to_date:  Overlap ending date
    :param int cutting_timestep:  Time step to cut the file
    :param boolean partial: Resolve partial overlap if True

    """
    if partial:
        filename_attr = re.match(pattern, filename).groupdict()
        assert len(filename_attr['period_start']) == len(filename_attr['period_end'])
        from_timestamp = str(from_date)[:len(filename_attr['period_start'])]
        to_timestamp = str(to_date)[:len(filename_attr['period_end'])]
        tmp = filename.replace(filename_attr['period_start'], from_timestamp)
        new_filename = tmp.replace(filename_attr['period_end'], to_timestamp)
        assert not os.path.exists(os.path.join(directory, new_filename))
        nc = nco.Nco()
        nc.ncks(input=os.path.join(directory, filename),
                output=os.path.join(directory, new_filename),
                options='-O -d time,{},,1'.format(cutting_timestep))
    os.remove(os.path.join(directory, filename))


def create_nodes(ffp):
    """
    Creates the node into the corresponding Graph().
    One directed graph per dataset. Each file is analysed to be a node in its graph.
    A node is a filename with some attributes:

     * start = the start date of the file sub-period
     * end = the end date of the file sub-period
     * next = the date next to the end date depending on the frequency, the calendar, etc.
     * first_step = the first time axis step
     * last_step = the last time axis step
     * path = the file full path

    :param str ffp: The file full path to process

    """
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate filename handler
        fh = Filename(ffp=ffp)
        # Extract start and end dates from filename
        fh.get_start_end_dates(pattern=pattern,
                               calendar=ref_calendar)
        # Create corresponding DiGraph if not exist
        if not graph.has_graph(fh.id):
            graph.set_graph(fh.id)
        # Retrieve corresponding graph
        g = graph.get_graph(fh.id)
        # Update/add current file as node with dates as attributes
        g.add_node(fh.filename,
                   start=fh.start_date,
                   end=fh.end_date,
                   next=fh.next_date,
                   first_step=fh.first_timestep,
                   last_step=fh.last_timestep,
                   path=fh.ffp)
        logging.debug('Graph: {} :: Node {} (start={}, end={}, next={})'.format(fh.id,
                                                                                fh.filename,
                                                                                fh.start_date,
                                                                                fh.end_date,
                                                                                fh.next_date))
        # Update graph
        graph.set_graph(fh.id, g)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return None


def create_edges(id):
    """
    Creates the edges between nodes into the corresponding Graph().
    One directed graph per dataset.

     * Builds the "START" node with the appropriate edges to the nodes with the earliest start date
     * Builds the "END" node with the appropriate edges from the nodes with the latest end date
     * Builds edges between a node and its "backwards" nodes

    :param tuple graph_input: A tuple with the graph id, the graph object and the processing context

    """
    g = graph.get_graph(id)
    # Create edges with backward nodes
    # A node is a "backward" node when the difference between the next current time step
    # and its start date is positive.
    # To ensure continuity path, edges has to only exist with backward nodes.
    for node, next_date in g.nodes(data='next'):
        # Considering one node, get the others in the graph
        other_nodes = [x for x in g.nodes() if x is not node]
        # Get the start dates of the other nodes
        other_start_dates = [g.node[x]['start'] for x in other_nodes]
        # Find the index with a positive or null different between their start date and
        # the next date of the considered node
        indexes = [i for i, v in enumerate(next_date - np.array(other_start_dates)) if v >= 0]
        # Get all "next" nodes for the current node
        next_nodes = [other_nodes[i] for i in indexes]
        # For each next node, build the corresponding edge in the graph
        for next_node in next_nodes:
            g.add_edge(node, next_node)
            logging.debug('Graph: {} :: Edge {} --> {}'.format(id, node, next_node))
    # Find the node(s) with the earliest date
    start_dates = zip(*g.nodes(data='start'))[1]
    starts = [n for n in g.nodes() if g.nodes[n]['start'] == min(start_dates)]
    # Find the node(s) with the latest date
    end_dates = zip(*g.nodes(data='end'))[1]
    ends = [n for n in g.nodes() if g.nodes[n]['end'] == max(end_dates)]
    # Build starting node with edges to first node(s)
    for start in starts:
        g.add_edge('START', start)
        logging.debug('Graph: {} :: Edge START --> {}'.format(id, start))
    # Build ending node with edges from latest node(s)
    for end in ends:
        g.add_edge(end, 'END')
        logging.debug('Graph: {} :: Edge {} --> END'.format(id, end))
    # Finally update graph
    graph.set_graph(id, g)


def evaluate_graph(id):
    """
    Evaluate the directed graph looking for a shortest path between "START" and "END" nodes.
    If a shorted path is found, it looks for the potential overlaps.
    Partial and full overlaps are supported.
    If no shortest path found, it creates a new node "BREAK" in the path.

    :param tuple graph_input: A tuple with the graph id, the graph object and the processing context

    """
    g = graph.get_graph(id)
    path = list()
    full_overlaps, partial_overlaps = None, None
    logging.debug('Process graph: {}'.format(id))
    # Walk through the graph
    try:
        # Find shortest path between oldest and latest dates
        path = nx.shortest_path(g, source='START', target='END')
        # Get overlaps
        full_overlaps, partial_overlaps = get_overlaps(g, path)
    except nx.NetworkXNoPath:
        for node in sorted(g.nodes()):
            if node not in ['START', 'END']:
                path.append(node)
                # A node is a "forward" node when the difference between the next current time step
                # and its start date is negative.
                # A path gap exists from a node when no edges exist with ALL "forwards" nodes.
                # Considering one node, get the others in the graph
                other_nodes = [x for x in g.nodes() if x not in ['START', node, 'END']]
                # Get the start dates of the other nodes
                other_start_dates = [g.node[x]['start'] for x in other_nodes]
                # Find the index with a negative or null difference between their start date and
                # the next date of the considered node
                indexes = [i for i, v in enumerate(g.node[node]['next'] - np.array(other_start_dates)) if v <= 0]
                # Get all "next" nodes for the current node
                next_nodes = [other_nodes[i] for i in indexes]
                # Find available targets from graph
                try:
                    avail_targets = zip(*g.edges(node))[1]
                except IndexError:
                    avail_targets = []
                # If no "forward" nodes in edges target = BREAK
                if not set(next_nodes).intersection(avail_targets):
                    path.append('BREAK')
    return path, full_overlaps, partial_overlaps


def format_path(path, partial_overlaps, full_overlaps):
    """
    Formats the message to print as a diagnostic.
    It walks through the evaluated path of the directed graph and print the filenames with useful info.

    :param list path: The node path as a result of the directed graph evaluation
    :param dict partial_overlaps: Dictionary of partial overlaps
    :param list full_overlaps: List of full overlapping files
    :returns: The formatted diagnostic to print
    :rtype: *str*

    """
    msg = ''
    for i in range(1, len(path) - 1):
        m = '  {}'.format(path[i])
        if partial_overlaps and path[i] in partial_overlaps:
            m = '[ {} <-- overlap from {} to {} ] '.format(path[i],
                                                           partial_overlaps[path[i]]['start'],
                                                           partial_overlaps[path[i]]['end_overlap'])
        msg += '\n{}'.format(m)
    if full_overlaps:
        for n in full_overlaps:
            m = '[ {} <-- to remove ]'.format(n)
            msg += '\n{}'.format(m)
    return msg


def process_context(_pattern, _ref_calendar, _graph):
    """
    Initialize process context by setting particular variables as global variables.

    :param str pattern: The filename pattern
    :param str _ref_calendar: The time calendar  to be used as reference for the simulation

    """
    global pattern, ref_calendar, graph
    pattern = _pattern
    ref_calendar = _ref_calendar
    graph = _graph


def run(args):
    """
    Main process that:

     * Instantiates processing context,
     * Deduces start, end and next date from each filenames,
     * Builds the DiGraph,
     * Detects the shortest path between dates if exists,
     * Detects broken path between dates if exists,
     * Removes the overlapping files.

    :param ArgumentParser args: Command-line arguments parser

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        print("Analysing data, please wait...\r")
        # Multiprocessing manager to shared Python objects between processes
        BaseManager.register('graph', Graph, exposed=('get_graph', 'has_graph', 'set_graph', '__call__'))
        manager = BaseManager()
        manager.start()
        # DiGraph creation
        global graph
        graph = manager.graph()
        # Init processes pool
        pool = Pool(processes=ctx.processes, initializer=process_context, initargs=(ctx.pattern,
                                                                                    ctx.tinit.calendar,
                                                                                    graph))
        # Process supplied files to create nodes in appropriate directed graph
        handlers = [x for x in pool.imap(create_nodes, ctx.sources)]
        # Close pool of workers
        pool.close()
        pool.join()
        ctx.scan_files = len(handlers)
        # Retrieve graph instance from multiprocessing manager
        # Process each directed graph to create appropriate edges
        _ = [x for x in itertools.imap(create_edges, graph())]
        # Evaluate each graph if a shortest path exist
        for path, partial_overlaps, full_overlaps in itertools.imap(evaluate_graph, graph()):
            # Format message about path
            msg = format_path(path, partial_overlaps, full_overlaps)
            # If broken time serie
            if 'BREAK' in path:
                ctx.broken = True
                logging.error('Time series broken: {}'.format(msg))
            else:
                # Print overlaps if exists
                if full_overlaps or partial_overlaps:
                    ctx.overlaps = True
                    logging.error('Shortest path found WITH overlaps: {}'.format(msg))
                else:
                    logging.info('Shortest path found without overlaps: {}'.format(msg))
            # Resolve overlaps
            if ctx.resolve:
                # Full overlapping files has to be deleted before partial overlapping files are truncated.
                for node in ctx.full_overlaps:
                    resolve_overlap(directory=ctx.directory,
                                    pattern=ctx.pattern,
                                    filename=node,
                                    partial=False)
                if not ctx.full_overlap_only:
                    for node in ctx.partial_overlaps:
                        resolve_overlap(directory=ctx.directory,
                                        pattern=ctx.pattern,
                                        filename=node,
                                        from_date=ctx.overlaps['partial'][node]['cutting_date'],
                                        to_date=ctx.overlaps['partial'][node]['end_date'],
                                        cutting_timestep=ctx.overlaps['partial'][node]['cutting_timestep'],
                                        partial=True)
