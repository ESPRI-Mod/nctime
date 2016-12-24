#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import logging
import os
import re
import sys
from datetime import datetime
from functools import wraps
from multiprocessing import Pool
from textwrap import fill

import numpy as np

import db
from constants import *
from handler import File
from nctime.utils import time, utils


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +-----------------------+-------------+---------------------------------+
    | Attribute             | Type        | Description                     |
    +=======================+=============+=================================+
    | *self*.directory      | *str*       | Variable to scan                |
    +-----------------------+-------------+---------------------------------+
    | *self*.write          | *boolean*   | True if write mode              |
    +-----------------------+-------------+---------------------------------+
    | *self*.force          | *boolean*   | True if force writing           |
    +-----------------------+-------------+---------------------------------+
    | *self*.verbose        | *boolean*   | True if verbose mode            |
    +-----------------------+-------------+---------------------------------+
    | *self*.project        | *str*       | MIP project                     |
    +-----------------------+-------------+---------------------------------+
    | *self*.db             | *str*       | Database path                   |
    +-----------------------+-------------+---------------------------------+
    | *self*.threads        | *int*       | Maximal threads number          |
    +-----------------------+-------------+---------------------------------+
    | *self*.checksum_type  | *str*       | The checksum type               |
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
        self.write = args.write
        self.force = args.force
        self.verbose = args.v
        self.project = args.project
        self.db = utils.path_switcher('db', args, default='{0}/{1}'.format(os.getcwd(), 'timeaxis.db'))
        cfg = utils.config_parse(args.i, self.project)
        self.threads = args.max_threads
        if self.threads == 0:
            if cfg.has_option('DEFAULT', 'max_threads') and cfg.get('DEFAULT', 'max_threads') != '':
                self.threads = cfg.get('DEFAULT', 'max_threads')
            else:
                self.threads = MAX_THREADS_DEFAULT
        self.checksum_type = str(cfg.get('DEFAULT', 'checksum_type'))
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


def counted(fct):
    """
    Decorator used to count all file process calls.

    :param callable fct: The function to monitor
    :returns: A wrapped function with a ``.called`` attribute
    :rtype: *callable*

    """

    @wraps(fct)  # Convenience decorator to keep the file_process docstring
    def wrapper(*args, **kwargs):
        wrapper.called += 1
        return fct(*args, **kwargs)

    wrapper.called = 0
    wrapper.__name__ = fct.__name__
    return wrapper


@counted
def process(inputs):
    """
    time_axis_processing(inputs)

    Time axis process that\:
     * Deduces start and end dates from filename,
     * Rebuilds the theoretical time axis (using frequency, calendar, etc.),
     * Compares the theoretical time axis with the time axis from the file,
     * Compares the last theoretical date with the end date from the filename,
     * Checks if the expected time units keep unchanged,
     * Checks the squareness and the consistency of time boundaries,
     * Rewrites (with ``--write`` mode) the new time axis,
     * Computes the new checksum if modified,
     * Traceback the status.

    :param tuple inputs: A tuple with the filename, the processing context and the time initialization
    :returns: The updated file handler instance
    :rtype: *nctime.axis.handler.File*

    """
    # Extract processing context and time initialization from input tuple
    filename, ctx, init = inputs

    # Instantiate file handle from input tuple
    handler = File(directory=ctx.directory,
                   filename=filename,
                   has_bounds=init.has_bounds)

    # Extract start and end dates from filename
    start, _, _ = handler.get_start_end_dates(pattern=ctx.pattern,
                                              frequency=init.frequency,
                                              units=init.funits,
                                              calendar=init.calendar)

    # Rebuild a theoretical time axis with high precision
    handler.time_axis_rebuilt = handler.build_time_axis(start=start,
                                                        inc=time.time_inc(init.frequency)[0],
                                                        input_units=init.funits,
                                                        output_units=init.tunits,
                                                        calendar=init.calendar,
                                                        is_instant=init.is_instant)

    # Check consistency between last time date and end date from filename
    if handler.last_date != handler.end_date:
        # Rebuild a theoretical time axis with low precision
        handler.time_axis_rebuilt = handler.build_time_axis(start=utils.trunc(start, 5),
                                                            inc=time.time_inc(init.frequency)[0],
                                                            input_units=init.funits,
                                                            output_units=init.tunits,
                                                            calendar=init.calendar,
                                                            is_instant=init.is_instant)
        if handler.last_date != handler.end_date:
            handler.status.append('003')
            logging.error('{0} - 003 - Last time step differs from end date from filename'.format(filename))
            if ctx.verbose:
                axe = fill(' | '.join(map(str, handler.time_axis.tolist())), width=100)
                logging.info('{0} - Time axis:\n {1}'.format(filename, axe))
                axe = fill(' | '.join(map(str, handler.time_axis_rebuilt.tolist())), width=100)
                logging.info('{0} - Theoretical axis:\n {1}'.format(filename, axe))
            return handler

    # Check consistency between instant time and time boundaries
    if init.is_instant and init.has_bounds:
        handler.status.append('004')
        logging.error('{0} - 004 - An instantaneous time axis should not embed time boundaries'.format(filename))

    # Check consistency between averaged time and time boundaries
    if not init.is_instant and not init.has_bounds:
        handler.status.append('005')
        logging.error('{0} - 005 - An averaged time axis should embed time boundaries'.format(filename))

    # Check time axis squareness
    if not np.array_equal(handler.time_axis_rebuilt, handler.time_axis):
        handler.status.append('001')
        logging.error('{0} - 001 - Mistaken time axis over one or several time steps'.format(filename))
    else:
        handler.status.append('000')
        logging.info('{0} - Time axis seems OK'.format(filename))

    # Check time boundaries squareness if needed
    if init.has_bounds:
        handler.time_bounds_rebuilt = handler.build_time_bounds(start=utils.trunc(start, 5),
                                                                inc=time.time_inc(init.frequency)[0],
                                                                input_units=init.funits,
                                                                output_units=init.tunits,
                                                                calendar=init.calendar)
        if not np.array_equal(handler.time_bounds_rebuilt, handler.time_bounds):
            handler.status.append('006')
            logging.error('{0} - 006 - Mistaken time bounds over one or several time steps'.format(filename))

    # Check consistency between time units
    if init.tunits != handler.time_units:
        handler.status.append('002')
        logging.error('{0} - 002 - Time units must be unchanged for the same dataset.'.format(filename))

     # Check consistency between time units
    if init.calendar != handler.calendar:
        handler.status.append('007')
        logging.error('{0} - 007 - Calendar must be unchanged for the same dataset.'.format(filename))

    # Rewrite time axis depending on checking
    if (ctx.write or ctx.force) and set(['004']).intersection(set(handler.status)):
        # Delete time bounds and bounds attribute from file if write of force mode
        handler.nc_var_delete(variable='time_bnds')
        handler.nc_att_delete(attribute='bounds', variable='time')

    # Rewrite time axis depending on checking
    if (ctx.write and set(['001', '002', '006', '007']).intersection(set(handler.status))) or ctx.force:
        handler.nc_var_overwrite('time', handler.time_axis_rebuilt)
        handler.nc_att_overwrite('units', 'time', init.tunits)
        handler.nc_att_overwrite('calendar', 'time', init.calendar)
        # Rewrite time boundaries if needed
        if init.has_bounds:
            handler.nc_var_overwrite('time_bnds', handler.time_bounds_rebuilt)

    # Compute checksum at the end of all modifications and after closing file
    if (ctx.write or ctx.force) and set(['001', '002', '004', '006', '007']).intersection(set(handler.status)):
        handler.new_checksum = handler.checksum(ctx.checksum_type)

    # Return file status
    return handler


def yield_inputs(ctx, tinit):
    """
    Yields all files to process within tuples with the processing context and the time initialization.

    :param nctime.axis.main.ProcessingContext ctx: The processing context
    :param nctime.utils.time.TimeInit tinit: The time initialization context
    :returns: Attach the processing context and the time initialization to a file processing as an iterator of tuples
    :rtype: *iter*

    """
    for filename in ctx.get_files_list():
        yield filename, ctx, tinit


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`process` call
    :rtype: *callable*
    :raises Error: When a thread-process failed preserving its traceback

    """
    filename, ctx, _ = inputs

    try:
        return process(inputs)
    except Exception as e:
        # Use verbosity to raise the whole threads traceback errors
        if not ctx.verbose:
            logging.error('{0} skipped\n{1}: {2}'.format(filename, e.__class__.__name__, e.message))
        else:
            logging.exception('{0} failed'.format(filename))
        return None


def main(args):
    """
    Main process that\:
     * Instanciates processing context,
     * Defines the referenced time properties,
     * Instanciates threads pools,
     * Prints or logs the time axis diagnostics.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context from command-line arguments
    ctx = ProcessingContext(args)
    logging.info('Time axis diagnostic started for {0}'.format(ctx.directory))
    # Set driving time properties (e.g., calendar, frequency and time units) from first file in directory
    tinit = time.TimeInit(ctx)
    # Process
    pool = Pool(int(ctx.threads))
    handlers = pool.imap(wrapper, yield_inputs(ctx, tinit))
    status = [] ; counter = 0
    # Persist diagnostics into database
    if ctx.db:
        # Check if database exists
        if not os.path.isfile(ctx.db):
            logging.warning('Database does not exist')
            db.create(ctx.db)
    # Commit each diagnostic as a new entry
    for handler in handlers:
        status.extend(handler.status)
        counter += 1
        if ctx.db:
            diagnostic = dict()
            diagnostic['creation_date'] = datetime.now()
            diagnostic.update(ctx.__dict__)
            diagnostic.update(tinit.__dict__)
            diagnostic.update(handler.__dict__)
            diagnostic['status'] = ','.join(handler.status)
            db.insert(ctx.db, diagnostic)
            logging.info('{0} - Diagnostic persisted into database'.format(handler.filename))
        if ctx.verbose:
            logging.info('-> Filename: {0}'.format(handler.filename))
            logging.info('Start: {0}'.format(handler.start_date))
            logging.info('End: {0}'.format(handler.end_date))
            logging.info('Last: {0}'.format(handler.last_date))
            logging.info('Time steps: {0}'.format(handler.length))
            logging.info('Is instant: {0}'.format(tinit.is_instant))
            logging.info('-> Time axis:')
            logging.info('{0}'.format(fill(' | '.join(map(str, handler.time_axis.tolist())), width=100)))
            logging.info('-> Theoretical axis:')
            logging.info('{0}'.format(fill(' | '.join(map(str, handler.time_axis_rebuilt.tolist())), width=100)))
    # Close tread pool
    pool.close()
    pool.join()
    if any([s in EXIT_ERRORS for s in status]):
        logging.error('Some time axis should be corrected manually ({0} files scanned)'.format(counter))
        sys.exit(1)
    else:    
        logging.info('Time diagnostic completed ({0} files scanned)'.format(counter))
        sys.exit(0)

