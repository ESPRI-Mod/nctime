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
import sys
from importlib import import_module

from utils.constants import *
from utils.misc import init_logging
from utils.parser import MultilineFormatter, DirectoryChecker, regex_validator, keyval_converter

__version__ = 'v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    ############################
    # Main parser for "nctime" #
    ############################
    main = argparse.ArgumentParser(
        prog='nctime',
        description=PROGRAM_DESC,
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog=EPILOG)
    main._optionals.title = OPTIONAL
    main._positionals.title = POSITIONAL
    main.add_argument(
        '-h', '--help',
        action='help',
        help=HELP)
    main.add_argument(
        '-v',
        action='version',
        version='%(prog)s ({})'.format(__version__),
        help=VERSION_HELP)
    subparsers = main.add_subparsers(
        title=SUBCOMMANDS,
        dest='cmd',
        metavar='',
        help='')

    #######################################
    # Parent parser with common arguments #
    #######################################
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP)
    parent.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help=PROJECT_HELP)
    parent.add_argument(
        '-i',
        metavar='/esg/config/esgcet',
        type=str,
        default='/esg/config/esgcet',
        help=INI_HELP)
    parent.add_argument(
        '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    parent.add_argument(
        '-h', '--help',
        action='help',
        help=HELP)
    parent.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=str,
        default='^.*/\.[\w]*.*$',
        help=IGNORE_DIR_HELP)
    parent.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    parent.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    group = parent.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    group.add_argument(
        '--errors-only',
        action='store_true',
        default=False,
        help=ERRORS_ONLY_HELP)
    parent.add_argument(
        '--max-processes',
        metavar='INT',
        type=int,
        help=MAX_PROCESSES_HELP)
    parent.add_argument(
        '--set-inc',
        metavar='FREQUENCY=INCREMENT',
        type=keyval_converter,
        action='append',
        help=SET_INC_HELP)

    ##################################
    # Subparser for "nctime overlap" #
    ##################################
    overlap = subparsers.add_parser(
        'overlap',
        prog='nctime overlap',
        description=OVERLAP_DESC,
        formatter_class=MultilineFormatter,
        help=OVERLAP_HELP,
        add_help=False,
        parents=[parent])
    overlap._optionals.title = OPTIONAL
    overlap._positionals.title = POSITIONAL
    overlap.add_argument(
        '--resolve',
        action='store_true',
        default=False,
        help=RESOLVE_HELP)
    overlap.add_argument(
        '--full-overlap-only',
        action='store_true',
        default=False,
        help=FULL_OVERLAP_ONLY_HELP)

    ###############################
    # Subparser for "nctime axis" #
    ###############################
    axis = subparsers.add_parser(
        'axis',
        prog='nctime axis',
        description=AXIS_DESC,
        formatter_class=MultilineFormatter,
        help=AXIS_HELP,
        add_help=False,
        parents=[parent])
    axis._optionals.title = OPTIONAL
    axis._positionals.title = POSITIONAL
    axis.add_argument(
        '--write',
        action='store_true',
        default=False,
        help=WRITE_HELP)
    axis.add_argument(
        '--force',
        action='store_true',
        default=False,
        help=FORCE_HELP)
    axis.add_argument(
        '--on-fly',
        action='store_true',
        default=False,
        help=ON_FLY_HELP)
    return main.parse_args()


def run():
    # Get command-line arguments
    args = get_args()
    # Initialize logger
    if args.errors_only:
        level = 'ERROR'
    elif args.debug:
        level = 'DEBUG'
    else:
        level = 'INFO'
    init_logging(log=args.log, level=level)
    # Run program
    main = import_module('.main', package='nctime.{}'.format(args.cmd))
    main.run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    run()
