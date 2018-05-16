#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import logging
import os
import re

import numpy as np
from netcdftime import datetime

import db
from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.misc import trunc
from nctime.utils.time import truncated_timestamp

def process(collector_input):
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

    :param tuple collector_input: A tuple with the file path and the processing context
    :returns: The updated file handler instance
    :rtype: *nctime.axis.handler.File*

    """
    # Deserialize inputs from collector
    ffp, ctx = collector_input
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp=ffp,
                  pattern=ctx.pattern,
                  ref_units=ctx.tinit.tunits,
                  ref_calendar=ctx.tinit.calendar)
        last_date = fh.get_last_date(fh.start_date)
        last_timestamp = truncated_timestamp(last_date, fh.timestamp_length)
        # In the case of inconsistent timestamps, it may be due to float precision issue
        if not ctx.on_fly and last_timestamp != fh.end_timestamp:
            fh.start_date = trunc(fh.start_date, 5)
            last_date = fh.get_last_date(fh.start_date)
            last_timestamp = truncated_timestamp(last_date, fh.timestamp_length)
            # Check consistency between last time date and end date from filename
            if last_timestamp != fh.end_timestamp:
                fh.status.append('003')
            elif last_date != fh.end_date:
                fh.status.append('008')
        # Rebuild a theoretical time axis with appropriate precision

        # TODO: Check heavy time axis by chunk
        # if fh.size > 1e9:
        #     chunks = fh.get_time_chunks()
        #     blocksize = os.stat(ffp).st_blksize
        #     for block in iter(lambda: f.read(blocksize), b''):
        #         fh.get_time_axis(chunk=chunk)


        fh.time_axis_rebuilt = fh.build_time_axis()
        # Check file consistency between instant time and time boundaries
        if fh.is_instant and fh.has_bounds:
            fh.status.append('004')
        # Check file consistency between averaged time and time boundaries
        if not fh.is_instant and not fh.has_bounds:
            fh.status.append('005')
        # Check time axis squareness
        if not np.array_equal(fh.time_axis_rebuilt, fh.time_axis):
            fh.status.append('001')
        else:
            fh.status.append('000')
        # Check time boundaries squareness
        if fh.has_bounds:
            fh.time_bounds_rebuilt = fh.build_time_bounds()
            if not np.array_equal(fh.time_bounds_rebuilt, fh.time_bounds):
                fh.status.append('006')
        # Check time units consistency between file and ref
        if ctx.tinit.tunits != fh.tunits:
            fh.status.append('002')
        # Check calendar consistency between file and ref
        if ctx.tinit.calendar != fh.calendar:
            fh.status.append('007')
        # Rename file depending on checking
        if (ctx.write or ctx.force) and {'003'}.intersection(set(fh.status)):
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp, last_timestamp, fh.filename))
        # Remove time boundaries depending on checking
        if (ctx.write or ctx.force) and {'004'}.intersection(set(fh.status)):
            # Delete time bounds and bounds attribute from file if write or force mode
            fh.nc_var_delete(variable=fh.tbnds)
            fh.nc_att_delete(attribute='bounds', variable='time')
        # Rewrite time axis depending on checking
        if (ctx.write and {'001', '002', '006', '007'}.intersection(set(fh.status))) or ctx.force:
            fh.nc_var_overwrite('time', fh.time_axis_rebuilt)
            fh.nc_att_overwrite('units', 'time', ctx.tinit.tunits)
            fh.nc_att_overwrite('calendar', 'time', ctx.tinit.calendar)
            # Rewrite time boundaries if needed
            if fh.has_bounds:
                fh.nc_var_overwrite(fh.time_bounds, fh.time_bounds_rebuilt)
        # Compute checksum at the end of all modifications and after closing file
        if (ctx.write or ctx.force) and {'001', '002', '003', '004', '006', '007'}.intersection(set(fh.status)):
            fh.new_checksum = fh.checksum(ctx.checksum_type)
        # Print file status
        msg = """{}
        Start: {} = {}
        End:   {} = {}
        Last:  {} = {}
        Time steps: {}
        Is instant: {}""".format(fh.filename,
                                 fh.start_timestamp, fh.start_date,
                                 fh.end_timestamp, fh.end_date,
                                 last_timestamp, last_date,
                                 fh.length,
                                 fh.is_instant)
        for s in fh.status:
            msg += """\n        Status: {}""".format(STATUS[s])
        if not {'000'}.intersection(set(fh.status)):
            logging.error(msg)
        else:
            logging.info(msg)
        # Return file status
        return fh
    except KeyboardInterrupt:
        raise
    except Exception as e:
        ctx.status.append('999')
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return None


def run(args):
    """
    Main process that:

     * Instantiates processing context,
     * Defines the referenced time properties,
     * Instantiates threads pools,
     * Prints or logs the time axis diagnostics.

    :param ArgumentParser args: Command-line arguments parser

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        print("Analysing data, please wait...\r")
        # Process supplied files
        handlers = [x for x in ctx.pool.imap(process, ctx.sources)]
        ctx.scan_files = len(handlers)
        # Persist diagnostics into database
        if ctx.db:
            # Check if database exists
            if not os.path.isfile(ctx.db):
                logging.warning('Database does not exist')
                db.create(ctx.db)
        # Commit each diagnostic as a new entry
        for handler in handlers:
            ctx.status.extend(handler.status)
            if ctx.db:
                diagnostic = dict()
                diagnostic['creation_date'] = datetime(1, 1, 1)._to_real_datetime().now().strftime("%Y%m%d-%H%M%S")
                diagnostic.update(ctx.__dict__)
                diagnostic.update(ctx.tinit.__dict__)
                diagnostic.update(handler.__dict__)
                diagnostic['status'] = ','.join(handler.status)
                db.insert(ctx.db, diagnostic)
                logging.info('{} - Diagnostic persisted into database'.format(handler.filename))
