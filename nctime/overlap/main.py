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

import nco
import networkx as nx
import numpy as np

from nctime.utils import time, utils


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +-----------------------+-------------+---------------------------------+
    | Attribute             | Type        | Description                     |
    +=======================+=============+=================================+
    | *self*.directory      | *str*       | Variable to scan                |
    +-----------------------+-------------+---------------------------------+
    | *self*.resolve        | *boolean*   | True to resolve overlaps        |
    +-----------------------+-------------+---------------------------------+
    | *self*.verbose        | *boolean*   | True if verbose mode            |
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
        self.resolve = args.resolve
        self.full_overlap_only = args.full_overlap_only
        self.verbose = args.v
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


def get_overlaps(ctx, nodes, shortest):
    """
    Returns all overlapping (default) files as a list of tuples. Each tuple gathers\:
     * The higher overlap bound,
     * The date to cut the file in order to resolve the overlap,
     * The corresponding cutting timestep.

    :param nctime.overlap.main.ProcessingContext ctx: The processing context
    :param dict() nodes: The directed graph nodes as a dictionary
    :param list shortest: The most consecutive files list (from `nx.DiGraph()`)
    :returns: The filenames
    :rtype: *list*

    """
    overlaps = dict()
    # Find partial overlapping nodes
    overlaps['partial'] = dict()
    for n in range(1, len(shortest)-2):
        # Get current node dates
        current_node = nodes[shortest[n]]
        # Get next node dates
        next_node = nodes[shortest[n+1]]
        # Because of the shortest path is selected, difference between bounds should always be positive or zero
        assert (current_node['next_date'] - next_node['start_date']) >= 0
        # Get partial overlap if exists
        # Partial overlap from next_node[1] to current_node[2] (bounds included)
        # Overlap is hold on the next node (arbitrary)
        print shortest[n], current_node['next_date']
        print shortest[n+1], next_node['start_date']
        if (current_node['next_date'] - next_node['start_date']) > 0:
            cutting_timestep = time.get_next_timestep(os.path.join(ctx.directory, shortest[n + 1]),
                                                      current_node['last_timestep'])
            overlaps['partial'][shortest[n + 1]] = next_node
            overlaps['partial'][shortest[n + 1]].update({'end_overlap': current_node['end_date'],
                                                         'cutting_date': current_node['next_date'],
                                                         'cutting_timestep': cutting_timestep})
    # Find full overlapping nodes
    overlaps['full'] = list(set(nodes.keys()).symmetric_difference(set(shortest[1:-1])))
    return overlaps


def resolve_overlap(ctx, filename, from_date=None, to_date=None, cutting_timestep=None, partial=False):
    """
    Resolve overlapping files.
    If full overlap, the corresponding file is removed.
    If partial overlap, the corresponding file is truncated into a new one and the old file is removed.

    :param nctime.overlap.main.ProcessingContext ctx: The processing context
    :param str filename: The filename
    :param int from_date: Overlap starting date
    :param int to_date:  Overlap ending date
    :param int cutting_timestep:  Time step to cut the file
    :param boolean partial: Resolve partial overlap if True

    """
    if partial:
        filename_attr = re.match(ctx.pattern, filename).groupdict()
        assert len(filename_attr['start_period']) == len(filename_attr['end_period'])
        from_timestamp = str(from_date)[:len(filename_attr['start_period'])]
        to_timestamp = str(to_date)[:len(filename_attr['end_period'])]
        tmp = filename.replace(filename_attr['start_period'], from_timestamp)
        new_filename = tmp.replace(filename_attr['end_period'], to_timestamp)
        assert not os.path.exists(os.path.join(ctx.directory, new_filename))
        nc = nco.Nco()
        nc.ncks(input=os.path.join(ctx.directory, filename),
                output=os.path.join(ctx.directory, new_filename),
                options='-O -d time,{0},,1'.format(cutting_timestep))
    os.remove(os.path.join(ctx.directory, filename))


def main(args):
    """
    Main process that\:
     * Instantiates processing context,
     * Deduces start, end and next date from each filenames,
     * Builds the DiGraph,
     * Detects the shortest path between dates if exists,
     * Removes the overlapping files.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(args)
    logging.info('Overlap diagnostic started for {0}'.format(ctx.directory))
    # Set driving time properties (e.g., calendar, frequency and time units) from first file in directory
    tinit = time.TimeInit(ctx)
    # DiGraph creation
    graph = nx.DiGraph()
    graph.clear()
    nodes = dict()
    logging.info('Create edges from source nodes to target nodes')
    for filename in ctx.get_files_list():
        # A node is defined by the filename, its start, end and next dates with its first and last timesteps.
        nodes[filename] = dict()
        # Get start, end and next date of each file
        dates = time.get_start_end_dates_from_filename(filename=filename,
                                                       pattern=ctx.pattern,
                                                       frequency=tinit.frequency,
                                                       calendar=tinit.calendar)
        nodes[filename]['start_date'], nodes[filename]['end_date'], nodes[filename]['next_date'] = time.dates2int(dates)
        # Get first and last time steps
        timesteps = time.get_first_last_timesteps(os.path.join(ctx.directory, filename))
        nodes[filename]['first_timestep'], nodes[filename]['last_timestep'] = timesteps

    # Build starting node
    start_dates = [nodes[n]['start_date'] for n in nodes]
    starts = [n for n in nodes if nodes[n]['start_date'] == min(start_dates)]
    for start in starts:
        graph.add_edge('START', start)
        if ctx.verbose:
            logging.info('{0} --> {1}'.format(' START '.center(len(ctx.ref) + 2, '-'),
                                              start.center(len(ctx.ref) + 2)))
    # Create graph edges with filenames only
    end_dates = [nodes[n]['end_date'] for n in nodes]
    for n in nodes:
        # Create a fake ending node from all latest files in case of overlaps
        if nodes[n]['end_date'] == max(end_dates):
            graph.add_edge(n, 'END')
            if ctx.verbose:
                logging.info('{0} --> {1}'.format(n.center(len(ctx.ref) + 2),
                                                  ' END '.center(len(ctx.ref) + 2, '-')))
        else:
            # Get index of the closest node
            # The closest node is the node with the smallest positive difference
            # between next current time step and all start dates
            other_nodes = [x for x in nodes if x is not n]
            start_dates = [nodes[x]['start_date'] for x in other_nodes]
            nxts = [i for i, v in enumerate(nodes[n]['next_date'] - np.array(start_dates)) if v >= 0]
            if nxts:
                for nxt in nxts:
                    graph.add_edge(n, other_nodes[nxt])
                    if ctx.verbose:
                        logging.info('{0} --> {1}'.format(n.center(len(ctx.ref) + 2),
                                                          other_nodes[nxt].center(len(ctx.ref) + 2)))
    # Walk through the graph
    try:
        # Find shortest path between oldest and latest dates
        shortest = nx.shortest_path(graph, source='START', target='END')
        logging.info('Shortest path found')
    except nx.NetworkXNoPath, e:
        logging.error('No shortest path found: {0}'.format(str(e)))
        logging.info('Overlap diagnostic completed')
        sys.exit(1)
    # Get overlaps
    overlaps = get_overlaps(ctx, nodes, shortest)
    # Print results
    logging.info('{0} --> {1}'.format(' START '.center(len(ctx.ref) + 2, '-'),
                                      shortest[1].center(len(ctx.ref) + 2)))
    for i in range(1, len(shortest) - 2):
        if shortest[i+1] in overlaps['partial']:
            logging.info('{0} --> {1} < '
                         'overlap from {2} to {3}'.format(shortest[i].center(len(ctx.ref) + 2),
                                                          shortest[i + 1].center(len(ctx.ref) + 2),
                                                          overlaps['partial'][shortest[i+1]]['start_date'],
                                                          overlaps['partial'][shortest[i+1]]['end_overlap']))
        else:
            logging.info('{0} --> {1}'.format(shortest[i].center(len(ctx.ref) + 2),
                                              shortest[i + 1].center(len(ctx.ref) + 2)))
    logging.info('{0} --> {1}'.format(shortest[-2].center(len(ctx.ref) + 2),
                                      ' END '.center(len(ctx.ref) + 2, '-')))
    if all(not l for l in overlaps.values()):
        logging.info('No overlapping files')
    else:
        # Full overlapping files has to be deleted before partial overlapping files are truncated.
        if overlaps['full']:
            logging.warning('Full overlapping files:')
            for node in overlaps['full']:
                if ctx.resolve:
                    resolve_overlap(ctx, node, partial=False)
                    logging.warning('{0} > REMOVED'.format(node))
                else:
                    logging.warning(node)
        if overlaps['partial']:
            logging.warning('Partial overlapping files:')
            for node in overlaps['partial']:
                if ctx.resolve and not ctx.full_overlap_only:
                    resolve_overlap(ctx,
                                    filename=node,
                                    from_date=overlaps['partial'][node]['cutting_date'],
                                    to_date=overlaps['partial'][node]['end_date'],
                                    cutting_timestep=overlaps['partial'][node]['cutting_timestep'],
                                    partial=True)
                    logging.warning('{0} > TRUNCATED'.format(node))
                else:
                    logging.warning(node)
    logging.info('Overlap diagnostic completed')
