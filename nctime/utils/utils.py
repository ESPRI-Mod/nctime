#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   :platform: Unix
   :synopsis: Useful functions to use with this package.

"""

import ConfigParser
import logging
import os
import re
import textwrap
from argparse import HelpFormatter, ArgumentTypeError
from datetime import datetime

from constants import *
from exceptions import *


class MultilineFormatter(HelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __init__(self, prog):
        # Overload the HelpFormatter class.
        super(MultilineFormatter, self).__init__(prog, max_help_position=60, width=100)

    def _fill_text(self, text, width, indent):
        # Rewrites the _fill_text method to support multiline description.
        text = self._whitespace_matcher.sub(' ', text).strip()
        multiline_text = ''
        paragraphs = text.split('|n|n ')
        for paragraph in paragraphs:
            lines = paragraph.split('|n ')
            for line in lines:
                formatted_line = textwrap.fill(line, width,
                                               initial_indent=indent,
                                               subsequent_indent=indent) + '\n'
                multiline_text += formatted_line
            multiline_text += '\n'
        return multiline_text

    def _split_lines(self, text, width):
        # Rewrites the _split_lines method to support multiline helps.
        text = self._whitespace_matcher.sub(' ', text).strip()
        lines = text.split('|n ')
        multiline_text = []
        for line in lines:
            multiline_text.append(textwrap.fill(line, width))
        multiline_text[-1] += '\n'
        return multiline_text


class CfgParser(ConfigParser.ConfigParser):
    """
    Custom ConfigParser class

    """

    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        self.read_paths = list()

    def options(self, section, defaults=True, **kwargs):
        """
        Can get options() with/without defaults.

        """
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise ConfigParser.NoSectionError(section)
        if defaults:
            opts.update(self._defaults)
        if '__name__' in opts:
            del opts['__name__']
        return opts.keys()

    def read(self, filenames):
        """
        Read and parse a filename or a list of filenames, and records there paths.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            self._read(fp, filename)
            fp.close()
            self.read_paths.append(filename)


def init_logging(log, level='INFO'):
    """
    Initiates the logging configuration (output, date/message formatting).
    If a directory is submitted the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``If ``None`` the standard output is used.

    :param str log: The logfile name or directory.
    :param str level: The log level.

    """
    log_fmt = '%(asctime)s %(levelname)s %(message)s'
    log_date_fmt = '%Y/%m/%d %I:%M:%S %p'
    log_levels = {'CRITICAL': logging.CRITICAL,
                      'ERROR':    logging.ERROR,
                      'WARNING':  logging.WARNING,
                      'INFO':     logging.INFO,
                      'DEBUG':    logging.DEBUG,
                      'NOTSET':   logging.NOTSET}
    if log:
        if os.path.isfile(log):
            logging.basicConfig(filename=log,
                                level=log_levels[level],
                                format=log_fmt,
                                datefmt=log_date_fmt)
        else:
            logfile = 'timeaxis-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"),
                                                   os.getpid())
            if not os.path.isdir(log):
                os.makedirs(log)
            logging.basicConfig(filename=os.path.join(log, logfile),
                                level=log_levels[level],
                                format=log_fmt,
                                datefmt=log_date_fmt)
    else:
        logging.basicConfig(level=log_levels[level],
                            format=log_fmt,
                            datefmt=log_date_fmt)


def directory_checker(path):
    """
    Checks if the supplied directory exists. The path is normalized without trailing slash.

    :param str path: The path list to check
    :returns: The same path list
    :rtype: *str*
    :raises Error: If one of the directory does not exist

    """
    path = os.path.abspath(os.path.normpath(path))
    if not os.path.isdir(path):
        msg = "No such directory: '{0}'".format(path)
        raise ArgumentTypeError(msg)
    return path


def path_switcher(flag, args, default=os.getcwd()):
    """
    Switch to the appropriate path depending on the flag value.
    If simple flag without path, the path is read from configuration file.
    If no path is declared into configuration file, a default path is set.
    If the flag is combined with a path, this path is used.
    No flag is no path.

    :param str flag: The argument to evaluate
    :param *ArgumentParser* args: The corresponding ``argparse`` Namespace
    :param str default: The default path to set if not supplied
    :returns: The appropriate path
    :rtype: *str*
    """
    cfg = config_parse(args.i, args.project)
    option = '{0}_path'.format(flag)
    if args.__dict__[flag] == 'NO_PATH':
        if cfg.has_option('DEFAULT', option) and cfg.get('DEFAULT', option) != '':
            return cfg.get('DEFAULT', option)
        else:
            return default
    else:
        return args.__dict__[flag]


def config_parse(path, section):
    """
    Parses the configuration file if exists. Tests if required options are declared.

    :param str path: The absolute or relative path of the configuration file
    :param str section: The section to parse
    :returns: The configuration file parser
    :rtype: *ConfigParser*
    :raises Error: If no configuration file exists or is empty
    :raises Error: If section is missing
    :raises Error: If required options are missing
    :raises Error: If the configuration file parsing fails

    """
    path = os.path.abspath(os.path.normpath(path))
    if not os.path.isfile(path):
        raise NoConfigFile(path)
    cfg = CfgParser()
    cfg.read(path)
    if section not in cfg.sections():
        raise NoConfigSection(section, path)
    if not cfg:
        raise EmptyConfigFile(path)
    for option in REQUIRED_OPTIONS:
        if not cfg.has_option(section, option):
            raise NoConfigOption(option, section, cfg.read_paths)
    return cfg


def translate_filename_format(cfg, project_section):
    """
    Return a list of regular expression filters associated with the ``directory_format`` option
    in the configuration file. This can be passed to the Python ``re`` methods.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str project_section: The project section name to parse
    :returns: The corresponding ``re`` pattern

    """
    # Start translation
    pattern = cfg.get(project_section, 'filename_format', raw=True).strip()
    pattern = pattern.replace('\.', '__ESCAPE_DOT__')
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('__ESCAPE_DOT__', r'\.')
    # Translate period dates
    pattern = re.sub(re.compile(r'%\((start_period)\)s'), r'(?P<\1>[\d]+)', pattern)
    pattern = re.sub(re.compile(r'%\((end_period)\)s'), r'(?P<\1>[\d]+)', pattern)
    # Translate all patterns matching %(name)s
    pattern = re.sub(re.compile(r'%\(([^()]*)\)s'), r'(?P<\1>[\w.-]+)', pattern)
    return '^{0}$'.format(pattern)


def trunc(f, n):
    """
    Truncates a float f to n decimal places before rounding

    :param float f: The number to truncates
    :param int n: Decimal number to place before rounding
    :returns: The corresponding truncated number
    :rtype: *float*

    """
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])


def find_key(dic, val):
    """
    Returns the dictionary key given the value.

    :param str val: The value to search
    :param dict dic: The dictionnary
    :returns: The dictionnary key corresponding to the value
    :rtype: *str*

    """
    return [k for k, v in dic.iteritems() if v == val][0]
