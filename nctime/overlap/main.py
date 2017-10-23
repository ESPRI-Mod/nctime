#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Highlight chunked NetCDF files producing overlap in a time series.

"""

import logging
import os
import re

import nco
import networkx as nx
import numpy as np

from context import ProcessingContext
from nctime.utils.time import get_next_timestep, get_start_end_dates_from_filename, \
    get_first_last_timesteps, dates2int
from itertools import combinations, permutations

def get_overlaps(directory, nodes, shortest):
    """
    Returns all overlapping (default) files as a list of tuples. Each tuple gathers\:
     * The higher overlap bound,
     * The date to cut the file in order to resolve the overlap,
     * The corresponding cutting timestep.

    :param str directory: The directory scanned
    :param dict nodes: The directed graph nodes as a dictionary
    :param list shortest: The most consecutive files list (from `nx.DiGraph()`)
    :returns: The filenames
    :rtype: *list*

    """
    overlaps = dict()
    # Find partial overlapping nodes
    overlaps['partial'] = dict()
    for n in range(1, len(shortest) - 2):
        # Get current node dates
        current_node = nodes[shortest[n]]
        # Get next node dates
        next_node = nodes[shortest[n + 1]]
        # Because of the shortest path is selected, difference between bounds should always be positive or zero
        assert (current_node['next_date'] - next_node['start_date']) >= 0
        # Get partial overlap if exists
        # Partial overlap from next_node[1] to current_node[2] (bounds included)
        # Overlap is hold on the next node (arbitrary)
        if (current_node['next_date'] - next_node['start_date']) > 0:
            cutting_timestep = get_next_timestep(os.path.join(directory, shortest[n + 1]),
                                                 current_node['last_timestep'])
            overlaps['partial'][shortest[n + 1]] = next_node
            overlaps['partial'][shortest[n + 1]].update({'end_overlap': current_node['end_date'],
                                                         'cutting_date': current_node['next_date'],
                                                         'cutting_timestep': cutting_timestep})
    # Find full overlapping nodes
    overlaps['full'] = list(set(nodes.keys()).symmetric_difference(set(shortest[1:-1])))
    return overlaps['full'], overlaps['partial']


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
    for directory in args.directory:
        # Instantiate processing context
        with ProcessingContext(args, directory) as ctx:
            logging.info('Overlap diagnostic started for {}'.format(ctx.directory))
            ctx.graph.clear()
            nodes = dict()
            logging.info('Create edges from source nodes to target nodes')
            for ffp in ctx.sources:
                filename = os.path.basename(ffp)
                # A node is defined by the filename, its start, end and next dates with its first and last timesteps.
                nodes[filename] = dict()
                # Get start, end and next date of each file
                dates = get_start_end_dates_from_filename(filename=filename,
                                                          pattern=ctx.pattern,
                                                          frequency=ctx.tinit.frequency,
                                                          calendar=ctx.tinit.calendar)
                nodes[filename]['start_date'], nodes[filename]['end_date'], nodes[filename]['next_date'] = dates2int(
                    dates)
                # Get first and last time steps
                timesteps = get_first_last_timesteps(ffp)
                nodes[filename]['first_timestep'], nodes[filename]['last_timestep'] = timesteps

            # Build starting node
            start_dates = [nodes[n]['start_date'] for n in nodes]
            starts = [n for n in nodes if nodes[n]['start_date'] == min(start_dates)]
            for start in starts:
                ctx.graph.add_edge('START', start)
                if ctx.verbose:
                    logging.info('{} --> {}'.format(' START '.center(ctx.display + 2, '-'),
                                                    start.center(ctx.display + 2)))
            # Create graph edges with filenames only
            end_dates = [nodes[n]['end_date'] for n in nodes]
            other_nodes = []
            for n in nodes:
                # Create a fake ending node from all latest files in case of overlaps
                if nodes[n]['end_date'] == max(end_dates):
                    ctx.graph.add_edge(n, 'END')
                    if ctx.verbose:
                        logging.info('{} --> {}'.format(n.center(ctx.display + 2),
                                                        ' END '.center(ctx.display + 2, '-')))
                else:
                    # A node is a "backward" node when the difference between the next current time step
                    # and its start date is positive.
                    # To ensure continuity path, edges has to only exist with backward nodes.
                    other_nodes = [x for x in nodes if x is not n]
                    start_dates = [nodes[x]['start_date'] for x in other_nodes]
                    # Find index of "backwards" nodes
                    nxts = [i for i, v in enumerate(nodes[n]['next_date'] - np.array(start_dates)) if v >= 0]
                    nxts = [other_nodes[i] for i in nxts]
                    for nxt in nxts:
                        ctx.graph.add_edge(n, nxt)
                        if ctx.verbose:
                            logging.info('{} --> {}'.format(n.center(ctx.display + 2),
                                                            nxt.center(ctx.display + 2)))
            # Walk through the graph
            try:
                # Find shortest path between oldest and latest dates
                ctx.path = nx.shortest_path(ctx.graph, source='START', target='END')
                # Get overlaps
                ctx.full_overlaps, ctx.partial_overlaps = get_overlaps(ctx.directory, nodes, ctx.path)
            except nx.NetworkXNoPath:
                ctx.broken = True
                ctx.path.append('START')
                for n in sorted(nodes.keys()):
                    ctx.path.append(n)
                    # A node is a "forward" node when the difference between the next current time step
                    # and its start date is negative.
                    # A path gap exists from a node when no edges exist with ALL "forwards" nodes.
                    other_nodes = [x for x in nodes if x is not n]
                    start_dates = [nodes[x]['start_date'] for x in other_nodes]
                    # Find index of "forward" nodes
                    nxts = [i for i, v in enumerate(nodes[n]['next_date'] - np.array(start_dates)) if v <= 0]
                    nxts = [other_nodes[i] for i in nxts]
                    # Find available targets from graph
                    try:
                        avail_targets = zip(*ctx.graph.edges(n))[1]
                    except IndexError:
                        avail_targets = []
                    # If no "forward" nodes in edges target = BREAK
                    if not set(nxts).intersection(avail_targets):
                        ctx.path.append('BREAK')
                ctx.path.append('END')
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
