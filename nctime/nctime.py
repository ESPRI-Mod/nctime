#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: nctime
    :platform: Unix
    :synopsis: Toolbox to diagnose NetCDF time axis.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.jussieu.fr>

"""

import argparse
import os
from datetime import datetime

from utils.utils import MultilineFormatter, init_logging, directory_checker, path_switcher

# Program version
__version__ = 'v{0} {1}'.format('3.9.3', datetime(year=2016, month=12, day=23).strftime("%Y-%d-%m"))


def get_args():
    """
    Returns parsed command-line arguments. See ``nctime -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace
    :rtype: *ArgumentParser*

    """
    #############################
    # Main parser for "esgprep" #
    #############################
    main = argparse.ArgumentParser(
        prog='nctime',
        description="""
        NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely
        used following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and
        time are included in NetCDF files as vectors.|n|n

        The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate
        models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse,
        produced erroneous results, due to problems in the time axis description.|n|n

        Moreover, to produce smaller files, the NetCDF files are splitted over the time period. Consequently, the
        different MIP archives designs include the period dates into the filename. The scheme of chunked files in MIP
        projects is not fixed and depends on several parameters (the institute, the model, the frequency, etc.). These
        different schemes lead to unnecessary overlapping files with a more complex folder reading and wasting disk
        space.|n|n

        "nctime" is a Python toolbox allowing you to easily:|n
         - Highlight chunked NetCDF files producing overlaps in a time series and delete all chunked overlapping
         files,|n
         - Check and rebuild a MIP-compliant time axis of your NetCDF files.|n|n

        Note that "nctime" is based on uncorrupted filename period dates and properly-defined times units, time
        calendar and frequency NetCDF attributes.|n|n

        See full documentation and references on http://nctime.readthedocs.io/.
        """,
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""
        Developed by:|n
        Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)
        """)
    main._optionals.title = "Optional arguments"
    main._positionals.title = "Positional arguments"
    main.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    main.add_argument(
        '-V',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    subparsers = main.add_subparsers(
        title='Tools as subcommands',
        dest='cmd',
        metavar='',
        help='')

    #######################################
    # Parent parser with common arguments #
    #######################################
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        'directory',
        type=directory_checker,
        nargs='?',
        help="""Variable path to diagnose.""")
    parent.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""
        Required project name corresponding to a section of the|n
        configuration file.
        """)
    parent.add_argument(
        '-i',
        metavar='$PWD/config.ini',
        type=str,
        default='{0}/config.ini'.format(os.getcwd()),
        help="""Path of configuration INI file.""")
    parent.add_argument(
        '--log',
        metavar='<log_dir>',
        type=str,
        const='NO_PATH',
        nargs='?',
        help="""
        Logfile directory. <log_dir> is read from configuration |n
        file if not submitted. If no <log_dir>, current working |n
        directory is used instead. An existing logfile can be submitted.|n
        If not, standard output is used.
        """)
    parent.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    parent.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")

    ##################################
    # Subparser for "nctime overlap" #
    ##################################
    overlap = subparsers.add_parser(
        'overlap',
        prog='nctime overlap',
        description="""
        To produce smaller files, the NetCDF files are splited over the time period. Consequently, the different MIP
        archives designs include the period dates into the filename.|n|n

        The scheme of chunked files in MIP projects is not fixed and depends on several parameters (the institute,
        the model, the frequency, etc.). These different schemes lead to unnecessary overlapping files with a more
        complex folder reading and wasting disk space.|n|n

        "overlap" is a command-line tool allowing you to easily highlight chunked NetCDF files producing overlaps in
        a time series and delete all chunked overlapping files in your MIP variable directories in order to save
        disk space.|n|n

        Note that:|n (i) Only complete overlaps are detected. For example, if a file goes from 1991 to 2010 and
        another goes from 2001 to 2020, the overap is partial. If the second file goes from 2001 to 2010 so the
        overlap is complete and the second file can be removed without loss of information.|n (ii) "overlap" is
        based on uncorrupted filename period dates and properly-defined times units, time calendar and frequency
        NetCDF attributes.|n|n

        The default values are displayed next to the corresponding flags.
        """,
        formatter_class=MultilineFormatter,
        help="""
        Highlight chunked NetCDF files producing overlap in a time series.|n
        See "nctime overlap -h" for full help.""",
        add_help=False,
        parents=[parent])
    overlap._optionals.title = "Optional arguments"
    overlap._positionals.title = "Positional arguments"
    overlap.add_argument(
        '--mip',
        metavar='*',
        nargs='?',
        default='*',
        help="""
        Specifies a MIP table value so as to filter directory|n
        content (Unix wildcard are allowed).
        """)
    overlap.add_argument(
        '--remove',
        action='store_true',
        default=False,
        help="""
        Removes overlapping files.|n
        THIS ACTION DEFINITELY MODIFY INPUT DIRECTORY!
        """)
    overlap.add_argument(
        '--subtree',
        action='store_true',
        default=False,
        help="""If a period gap, use the sub-period from the start date.""")

    ###############################
    # Subparser for "nctime axis" #
    ###############################
    axis = subparsers.add_parser(
        'axis',
        prog='nctime axis',
        description="""
        NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely
        used following the CF conventions. Dimensions such as longitude, latitude and time are included in NetCDF
        files as vectors.|n|n

        The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled
        climate models and leads to flawed studies or unused data.|n|n

        "time_axis" is a command-line tool allowing you to easily check and rebuild a MIP-compliant time axis of
        your downloaded files from the ESGF.|n|n

        Note that:|n
        (i) "time_axis" is based on uncorrupted filename period dates and properly-defined times units, time
        calendar and frequency NetCDF attributes.|n
        (ii) To rebuild a proper time axis, the dates from filename are expected to set the first time boundary and
        not the middle of the time interval. This is always the case for the instantaneous axis or frequencies
        greater than the daily frequency. Consequently, the 3-6 hourly files with an averaged time axis requires a
        date time correction.|n|n

        Time axis status returned:|n
        000: Unmodified time axis,|n
        001: Corrected time axis because wrong time steps,|n
        002: Corrected time axis because of changing time units,|n
        003: Ignored time axis because of inconsistency between last date of time axis and end date of filename
        period (e.g., wrong time axis length),|n
        004: Corrected time axis deleting time boundaries for instant time,|n
        005: Ignored averaged time axis without time boundaries,|n
        006: Corrected time bounds because wrong time steps.|n|n

        The default values are displayed next to the corresponding flags.
        """,
        formatter_class=MultilineFormatter,
        help="""
        Rewrite and/or check time axis of MIP NetCDF files.|n
        See "nctime axis -h" for full help.
        """,
        add_help=False,
        parents=[parent])
    axis._optionals.title = "Optional arguments"
    axis._positionals.title = "Positional arguments"
    axis.add_argument(
        '--write',
        action='store_true',
        default=False,
        help="""
        Rewrites time axis depending on checking.|n
        THIS ACTION DEFINITELY MODIFY INPUT FILES!
        """)
    axis.add_argument(
        '--force',
        action='store_true',
        default=False,
        help="""
        Forces time axis writing overpassing checking step.|n
        THIS ACTION DEFINITELY MODIFY INPUT FILES!
        """)
    axis.add_argument(
        '--db',
        metavar='<db_path>',
        type=str,
        nargs='?',
        const='NO_PATH',
        help="""
        SQLite database path to persist diagnostics. <db_path> is |n
        read from configuration file if not submitted. If no <db_path>, |n
        current working directory is used instead. If not, time |n
        diagnostic is not saved.
        """)
    axis.add_argument(
        '--max-threads',
        metavar='<max_threads>',
        type=int,
        default=0,
        help="""
        Number of maximal threads to simultaneously process several |n
        files. If not, <max_threads> from configuration file is used.|n
        If no default <max_threads>, only one thread is used (i.e., |n
        sequential processing).
        """)

    return main.parse_args()


def run():
    # Get command-line arguments
    args = get_args()
    # Initialize logger
    args.log = path_switcher('log', args)
    if args.v:
        init_logging(args.log, level='DEBUG')
    else:
        init_logging(args.log)

    # Run subcommand
    if args.cmd == 'axis':
        from axis import main
        main.main(args)
    elif args.cmd == 'overlap':
        from overlap import main
        main.main(args)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
