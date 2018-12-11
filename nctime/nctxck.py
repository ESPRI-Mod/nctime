#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: nctxck
    :platform: Unix
    :synopsis: netCDF Time Axis Checker part of the toolbox to diagnose netCDF time axis.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.jussieu.fr>

"""

from nctime.axis.main import run

from utils.constants import *
from utils.help import *
from utils.parser import *

__version__ = 'from nctime v{} {}'.format(VERSION, VERSION_DATE)


def get_args(args=None):
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = CustomArgumentParser(
        prog='nctxck',
        description=PROGRAM_DESC['axis'],
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
    main.add_argument(
        '-p', '--project',
        metavar='PROJECT',
        type=str,
        help=PROJECT_HELP)
    main.add_argument(
        '-i',
        metavar='$ESGINI_DIR',
        type=str,
        default=os.environ['ESGINI_DIR'] if 'ESGINI_DIR' in os.environ.keys() else '/esg/config/esgcet',
        help=INI_HELP)
    main.add_argument(
        '-l', '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    main.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    main.add_argument(
        'input',
        action=InputChecker,
        nargs='+',
        help=INPUT_HELP)
    main.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=str,
        default='^.*/\.[\w]*.*$',
        help=IGNORE_DIR_HELP)
    main.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    main.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    main.add_argument(
        '-w', '--write',
        action='store_true',
        default=False,
        help=WRITE_HELP)
    main.add_argument(
        '-f', '--force',
        action='store_true',
        default=False,
        help=FORCE_HELP)
    group = main.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--on-fly',
        action='store_true',
        default=False,
        help=ON_FLY_HELP)
    group.add_argument(
        '-c', '--card',
        action=DirectoryChecker,
        help=CARD_HELP)
    main.add_argument(
        '--set-inc',
        metavar='TABLE:FREQUENCY=INCREMENT',
        type=inc_converter,
        action='append',
        help=SET_INC_HELP)
    main.add_argument(
        '--calendar',
        action=CalendarChecker,
        default=None,
        help=CALENDAR_HELP)
    main.add_argument(
        '--units',
        action=TimeUnitsChecker,
        default=None,
        help=UNITS_HELP)
    main.add_argument(
        '--start',
        action=TimestampChecker,
        metavar='TIMESTAMP',
        default=None,
        help=START_HELP['axis'])
    main.add_argument(
        '--end',
        action=TimestampChecker,
        metavar='TIMESTAMP',
        default=None,
        help=END_HELP['axis'])
    main.add_argument(
        '-a', '--all',
        action='store_true',
        default=False,
        help=ALL_HELP)
    main.add_argument(
        '--limit',
        metavar='5',
        type=positive_only,
        default=5,
        nargs='?',
        help=LIMIT_HELP)
    main.add_argument(
        '--ignore-errors',
        action=CodeChecker,
        metavar='CODE',
        default='',
        help=IGNORE_ERROR_HELP)
    main.add_argument(
        '--max-processes',
        metavar='INT',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)
    group = main.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--color',
        action='store_true',
        help=COLOR_HELP)
    group.add_argument(
        '--no-color',
        action='store_true',
        help=NO_COLOR_HELP)
    return main.prog, main.parse_args(args)


def main(args=None):
    # Get command-line arguments
    prog, args = get_args(args)
    setattr(args, 'prog', prog)
    # Run program
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
