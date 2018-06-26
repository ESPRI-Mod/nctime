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

from utils.constants import *
from utils.parser import MultilineFormatter, DirectoryChecker, regex_validator, keyval_converter, processes_validator, \
    positive_only, InputChecker, CodeChecker, _ArgumentParser

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
    main = _ArgumentParser(
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
        '-p', '--project',
        metavar='PROJECT',
        type=str,
        help=PROJECT_HELP)
    parent.add_argument(
        '-i',
        metavar='$ESGINI',
        type=str,
        default=os.environ['ESGINI'] if 'ESGINI' in os.environ.keys() else '/esg/config/esgcet',
        help=INI_HELP)
    parent.add_argument(
        '-l', '--log',
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
        '--set-inc',
        metavar='FREQUENCY=INCREMENT',
        type=keyval_converter,
        action='append',
        help=SET_INC_HELP)
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
    parent.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    parent.add_argument(
        '-a', '--all',
        action='store_true',
        default=False,
        help=ALL_HELP)
    parent.add_argument(
        '--max-processes',
        metavar='INT',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)

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
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP)
    overlap.add_argument(
        '-r', '--resolve',
        action='store_true',
        default=False,
        help=RESOLVE_HELP)
    overlap.add_argument(
        '--full-only',
        action='store_true',
        default=False,
        help=FULL_ONLY_HELP)
    overlap.add_argument(
        '-c', '--card',
        action=DirectoryChecker,
        help=CARD_HELP)

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
        'input',
        action=InputChecker,
        nargs='+',
        help=DIRECTORY_HELP)
    axis.add_argument(
        '-w', '--write',
        action='store_true',
        default=False,
        help=WRITE_HELP)
    axis.add_argument(
        '-f', '--force',
        action='store_true',
        default=False,
        help=FORCE_HELP)
    group = axis.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--on-fly',
        action='store_true',
        default=False,
        help=ON_FLY_HELP)
    group.add_argument(
        '-c', '--card',
        action=DirectoryChecker,
        help=CARD_HELP)
    axis.add_argument(
        '--limit',
        metavar='5',
        type=positive_only,
        default=5,
        nargs='?',
        help=LIMIT_HELP)
    axis.add_argument(
        '--ignore-errors',
        action=CodeChecker,
        metavar='CODE',
        default='',
        help=IGNORE_ERROR_HELP)
    axis.add_argument(
        '--correct-timestamp',
        action='store_true',
        default=False,
        help=CORRECT_TIMESTAMP_HELP)
    return main.prog, main.parse_args()


def main():
    # Get command-line arguments
    prog, args = get_args()
    setattr(args, 'prog', prog)
    # Run program
    if args.cmd == 'overlap':
        from overlap.main import run
    else:
        from axis.main import run
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
