#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Highlight chunked NetCDF files producing overlap in a time series.

"""

import itertools
import os
import re
import sys
from multiprocessing import Pool
from xml.etree.ElementTree import parse

import nco
import networkx as nx
import numpy as np
from ESGConfigParser import ExpressionNotMatch

from constants import *
from context import ProcessingContext
from handler import Filename, Graph
from nctime.utils.misc import COLORS, ProcessContext
from nctime.utils.time import get_next_timestep


def get_overlaps(g, shortest):
    """
    Returns all overlapping files (default) as a list of tuples. Each tuple gathers\:
     * The higher overlap bound,
     * The date to cut the file in order to resolve the overlap,
     * The corresponding cutting timestep.

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
            echo.debug('\nPartial overlap found between {} and {}'.format(shortest[n], shortest[n + 1]))
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


def extract_dates(ffp):
    """
    Extract dates attributes from netCDF file..

     * start = the start date of the file sub-period
     * end = the end date of the file sub-period
     * next = the date next to the end date depending on the frequency, the calendar, etc.
     * first_step = the first time axis step
     * last_step = the last time axis step
     * path = the file full path

    :param str ffp: The file full path to process

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate filename handler
        fh = Filename(ffp=ffp)
        # Extract start and end dates from filename
        fh.get_start_end_dates(pattern=pctx.pattern,
                               calendar=pctx.ref_calendar)
        with pctx.lock:
            echo.debug('\nFile: {} :: Start={}, End={}, Next={}'.format(fh.filename,
                                                                        fh.start_date,
                                                                        fh.end_date,
                                                                        fh.next_date))
        return fh
    except KeyboardInterrupt:
        raise
    except Exception as e:
        msg = """\n{}\nSkipped: {}""".format(COLORS.HEADER + os.path.basename(ffp) + COLORS.ENDC,
                                             COLORS.FAIL + e.message + COLORS.ENDC)
        echo.error(msg, buffer=True)
        return None
    finally:
        # Print progress
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbfiles)
            msg = COLORS.OKGREEN + '\rProcess netCDF file(s): ' + COLORS.ENDC
            msg += '{}% | {}/{} files'.format(percentage, pctx.progress.value, pctx.nbfiles)
            echo.progress(msg)


def create_nodes(fh):
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

    :param handler.Filename fh: The filename handler

    """
    # Create corresponding DiGraph if not exist
    if not graph.has_graph(fh.id):
        graph.set_graph(fh.id)
    # Update/add current file as node with dates as attributes
    node = graph.add_node(fh.id,
                          fh.filename,
                          fh.start_date,
                          fh.end_date,
                          fh.next_date,
                          fh.ffp)
    echo.debug('\nGraph: {} :: Node {} (start={}, end={}, next={})'.format(fh.id,
                                                                           fh.filename,
                                                                           node['start'],
                                                                           node['end'],
                                                                           node['next']))


def create_edges(gid):
    """
    Creates the edges between nodes into the corresponding Graph().
    One directed graph per dataset.

     * Builds the "START" node with the appropriate edges to the nodes with the earliest start date
     * Builds the "END" node with the appropriate edges from the nodes with the latest end date
     * Builds edges between a node and its "backwards" nodes

    :param str gid: The graph id

    """
    g = graph.get_graph(gid)
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
            graph.add_edge(gid, node, next_node)
            echo.debug('\nGraph: {} :: Edge {} --> {}'.format(gid, node, next_node))
    # Find the node(s) with the earliest date
    start_dates = zip(*g.nodes(data='start'))[1]
    starts = [n for n in g.nodes() if g.nodes[n]['start'] == min(start_dates)]
    # Find the node(s) with the latest date
    end_dates = zip(*g.nodes(data='end'))[1]
    ends = [n for n in g.nodes() if g.nodes[n]['end'] == max(end_dates)]
    # Build starting node with edges to first node(s)
    for start in starts:
        graph.add_edge(gid, 'START', start)
        echo.debug('\nGraph: {} :: Edge START --> {}'.format(gid, start))
    # Build ending node with edges from latest node(s)
    for end in ends:
        graph.add_edge(gid, end, 'END')
        echo.debug('\nGraph: {} :: Edge {} --> END'.format(gid, end))


def evaluate_graph(gid):
    """
    Evaluate the directed graph looking for a shortest path between "START" and "END" nodes.
    If a shorted path is found, it looks for the potential overlaps.
    Partial and full overlaps are supported.
    If no shortest path found, it creates a new node "BREAK" in the path.

    :param str gid: The graph id

    """
    g = graph.get_graph(gid)
    path = list()
    full_overlaps, partial_overlaps = None, None
    echo.debug('\nProcess graph: {}'.format(gid))
    # Walk through the graph
    try:
        # Find shortest path between oldest and latest dates
        path = nx.shortest_path(g, source='START', target='END')
        # Get overlaps
        partial_overlaps, full_overlaps = get_overlaps(g, path)
    except nx.NetworkXNoPath:
        nodes = sorted(g.nodes())
        for node in nodes:
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
                # If no "forward" nodes in edges target and not last node = potential BREAK
                if not set(next_nodes).intersection(avail_targets) and node != nodes[-1]:
                    if patterns:
                        # Get gap start year from current node
                        gap_start_year = int(float(str(g.node[node]['next'])[:4]))
                        # Get gap end year from next node in list
                        gap_end_year = int(float(str(g.node[nodes[nodes.index(node) + 1]]['start'])[:4]))
                        # Get filename pattern to search into XML files
                        facets = re.compile(CMIP6_FILENAME_PATTERN).groupindex
                        try:
                            attributes = re.search(CMIP6_FILENAME_PATTERN, node).groupdict()
                        except:
                            raise ExpressionNotMatch(node, CMIP6_FILENAME_PATTERN)
                        filename_pattern = list()
                        for idx in sorted(facets.values()):
                            key = facets.keys()[facets.values().index(idx)]
                            if key not in IGNORED_FACETS:
                                filename_pattern.append(attributes[key])
                        filename_pattern = '_'.join(filename_pattern) + '_{}-{}'.format('%start_date%', '%end_date%')
                        if node.endswith('-clim.nc'):
                            filename_pattern += '-clim'
                        # Check into XML files in the gap period
                        for year in range(gap_start_year, gap_end_year):
                            if filename_pattern in patterns[str(year)]:
                                echo.debug('\nPattern found in XML :: Year = {} :: {}'.format(year, filename_pattern))
                                path.append('BREAK')
                            else:
                                path.append('XML GAP')
                    else:
                        # If no file card submitted, no patterns loaded = potential BREAK as real BREAK
                        path.append('BREAK')
    return path, partial_overlaps, full_overlaps


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
    for node in path:
        if node not in ['START', 'END']:
            m = '  {}'.format(node)
            if partial_overlaps and node in partial_overlaps:
                m = '[ {} <-- overlap from {} to {} ] '.format(node,
                                                               partial_overlaps[node]['start'],
                                                               partial_overlaps[node]['end_overlap'])
            msg += '\n{}'.format(m)
    if full_overlaps:
        for n in full_overlaps:
            m = '[ {} <-- to remove ]'.format(n)
            msg += '\n{}'.format(m)
    return msg


def yield_filedef(paths):
    """
    Yields all file definition produced by dr2xml as input for XIOS.

    :param list paths: The list of filedef path
    :returns: The dr2xml files
    :rtype: *iter*

    """
    for path in paths:
        for root, _, filenames in os.walk(path, followlinks=True):
            for filename in filenames:
                ffp = os.path.join(root, filename)
                if os.path.isfile(ffp) and re.search('^dr2xml_.*\.xml$', filename):
                    yield ffp


def get_patterns_from_filedef(path):
    """
    Parses dr2xml files.
    Each filename pattern is deserialized as a dictionary of facet: value.

    :param str path: The path to scan
    :returns: The filename deserialized with facets
    :rtype: *dict*

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    with pctx.lock:
        echo.debug(COLORS.OKGREEN + '\nParse XML filedef :: ' + COLORS.ENDC + '{}'.format(path))
    year = os.path.basename(os.path.dirname(path))
    xml_tree = parse(path)
    patterns = list()
    for item in xml_tree.iterfind('*/file'):
        # Get XML file_id entry name
        item = item.attrib['name'].strip()
        # Ignore "cfsites_grid" entry
        if item == 'cfsites_grid':
            continue
        with pctx.lock:
            echo.debug('\nProcess XML file_id entry :: {}'.format(item))
        patterns.append(item)
    # Print progress
    with pctx.lock:
        pctx.progress.value += 1
        percentage = int(pctx.progress.value * 100 / pctx.nbxml)
        msg = COLORS.OKGREEN + '\rProcess XML file(s): ' + COLORS.ENDC
        msg += '{}% | {}/{} files'.format(percentage,
                                          pctx.progress.value,
                                          pctx.nbxml)
        echo.progress(msg)
    return year, patterns


def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    :param list keys: Argument name list
    :param list values: Argument value list

    """
    assert len(keys) == len(values)
    global pctx
    pctx = ProcessContext({key: values[i] for i, key in enumerate(keys)})


def run(args=None):
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
    # Declare global variables
    global graph, echo, patterns
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Initialize print management
        echo = ctx.echo
        # Print command-line
        echo.command(COLORS.OKBLUE + 'Command: ' + COLORS.ENDC + ' '.join(sys.argv) + '\n')
        # Collecting data
        echo.progress('\rCollecting data, please wait...')
        # Get number of files
        ctx.nbfiles = len(ctx.sources)
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        if ctx.use_pool:
            # Init processes pool
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))
            # Process supplied files to create nodes in appropriate directed graph
            handlers = [x for x in pool.imap(extract_dates, ctx.sources) if x is not None]
            # Close pool of workers
            pool.close()
            pool.join()
        else:
            initializer(cctx.keys(), cctx.values())
            handlers = [x for x in itertools.imap(extract_dates, ctx.sources) if x is not None]
        ctx.skip = ctx.nbfiles - len(handlers)
        # Process XML files if card
        patterns = dict()
        if ctx.card:
            echo.progress('\n')
            # Reset progress counter
            cctx['progress'].value = 0
            # Get number of xml
            ctx.nbxml = len([x for x in yield_filedef(ctx.card)])
            cctx['nbxml'] = ctx.nbxml
            if ctx.use_pool:
                # Init processes pool
                pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(),
                                                                                        cctx.values()))
                for k, v in pool.imap(get_patterns_from_filedef, yield_filedef(ctx.card)):
                    if k not in patterns.keys():
                        patterns[k] = list()
                    patterns[k].extend(v)
                # Close pool of workers
                pool.close()
                pool.join()
            else:
                initializer(cctx.keys(), cctx.values())
                for k, v in itertools.imap(get_patterns_from_filedef, yield_filedef(ctx.card)):
                    if k not in patterns.keys():
                        patterns[k] = list()
                    patterns[k].extend(v)
        # Initialize Graph()
        graph = Graph()
        # Process filename handler to create nodes
        ctx.nbnodes = len([x for x in itertools.imap(create_nodes, handlers)])
        # Process each directed graph to create appropriate edges
        ctx.nbdsets = len([x for x in itertools.imap(create_edges, graph())])
        # Evaluate each graph if a shortest path exist
        echo.debug('\n')
        echo.progress('\n')
        for path, partial_overlaps, full_overlaps in itertools.imap(evaluate_graph, graph()):
            # Format message about path
            msg = format_path(path, partial_overlaps, full_overlaps)
            # If broken time serie
            if 'BREAK' in path:
                ctx.broken += 1
                echo.error(COLORS.FAIL + '\nTime series broken:' + COLORS.ENDC + '{}'.format(msg))
            elif 'XML GAP' in path:
                echo.success(COLORS.WARNING + '\nNo path found because of XML gap(s):' + COLORS.ENDC + '{}'.format(msg))
            else:
                # Print overlaps if exists
                if full_overlaps or partial_overlaps:
                    ctx.overlaps += 1
                    echo.error(COLORS.FAIL + '\nShortest path found WITH overlaps:' + COLORS.ENDC +
                               '{}'.format(msg))
                else:
                    echo.success(COLORS.OKGREEN + '\nShortest path found without overlaps:' + COLORS.ENDC +
                                 '{}'.format(msg))
            # Resolve overlaps
            if ctx.resolve:
                # Full overlapping files has to be deleted before partial overlapping files are truncated.
                for node in ctx.full_overlaps:
                    resolve_overlap(directory=ctx.directory,
                                    pattern=ctx.pattern,
                                    filename=node,
                                    partial=False)
                if not ctx.full_only:
                    for node in ctx.partial_overlaps:
                        resolve_overlap(directory=ctx.directory,
                                        pattern=ctx.pattern,
                                        filename=node,
                                        from_date=ctx.overlaps['partial'][node]['cutting_date'],
                                        to_date=ctx.overlaps['partial'][node]['end_date'],
                                        cutting_timestep=ctx.overlaps['partial'][node]['cutting_timestep'],
                                        partial=True)
    # Evaluate errors and exit with appropriate return code
    if ctx.overlaps or ctx.broken or ctx.nberrors:
        if (ctx.broken + ctx.overlaps + ctx.nberrors) == ctx.nbdsets:
            # All datasets has error(s). Error code = -1
            sys.exit(2)
        else:
            # Some datasets (at least one) has error(s). Error code = nb datasets with error(s)
            sys.exit(1)
    else:
        # No errors. Error code = 0
        sys.exit(0)


if __name__ == "__main__":
    run()
