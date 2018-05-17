#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import logging
import re
from multiprocessing import Pool, Lock

import numpy as np

from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.misc import trunc


def process(ffp):
    """
    Process time axis checkup and rewriting if needed.

    :param str ffp: The file full path to process
    :returns: The file status
    :rtype: *list*

    """
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp=ffp,
                  pattern=pattern,
                  ref_units=ref_units,
                  ref_calendar=ref_calendar)
        fh.load_last_date()
        # In the case of inconsistent timestamps, it may be due to float precision issue
        if not on_fly and fh.last_timestamp != fh.end_timestamp:
            fh.start_num = trunc(fh.start_num, 5)
            fh.load_last_date()
            # Check consistency between last time date and end date from filename
            if fh.last_timestamp != fh.end_timestamp:
                fh.status.append('003')
            elif fh.last_date != fh.end_date:
                fh.status.append('008')
        # Rebuild a theoretical time axis with appropriate precision
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
        if ref_units != fh.tunits:
            fh.status.append('002')
        # Check calendar consistency between file and ref
        if ref_calendar != fh.calendar:
            fh.status.append('007')
        # Rename file depending on checking
        if (write or force) and {'003'}.intersection(set(fh.status)):
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp, fh.last_timestamp, fh.filename))
        # Remove time boundaries depending on checking
        if (write or force) and {'004'}.intersection(set(fh.status)):
            # Delete time bounds and bounds attribute from file if write or force mode
            fh.nc_var_delete(variable=fh.tbnds)
            fh.nc_att_delete(attribute='bounds', variable='time')
        # Rewrite time axis depending on checking
        if (write and {'001', '002', '006', '007'}.intersection(set(fh.status))) or force:
            fh.nc_var_overwrite('time', fh.time_axis_rebuilt)
            fh.nc_att_overwrite('units', 'time', ref_units)
            fh.nc_att_overwrite('calendar', 'time', ref_calendar)
            # Rewrite time boundaries if needed
            if fh.has_bounds:
                fh.nc_var_overwrite(fh.time_bounds, fh.time_bounds_rebuilt)
        # Compute checksum at the end of all modifications and after closing file
        if (write or force) and {'001', '002', '003', '004', '006', '007'}.intersection(set(fh.status)):
            fh.new_checksum = fh.checksum()
        # Print file status
        msg = """{}
        Start: {} = {}
        End:   {} = {}
        Last:  {} = {}
        Time steps: {}
        Is instant: {}""".format(fh.filename,
                                 fh.start_timestamp, fh.start_date,
                                 fh.end_timestamp, fh.end_date,
                                 fh.last_timestamp, fh.last_date,
                                 fh.length,
                                 fh.is_instant)
        for s in fh.status:
            msg += """\n        Status: {}""".format(STATUS[s])
        # Acquire lock to standard output
        lock.acquire()
        if not {'000'}.intersection(set(fh.status)):
            logging.error(msg)
        else:
            logging.info(msg)
        # Release lock on standard output
        lock.release()
        # Return file status
        return fh.status
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return ['999']


def process_context(_pattern, _ref_units, _ref_calendar, _write, _force, _on_fly, _lock):
    """
    Initialize process context by setting particular variables as global variables.

    :param str _pattern: The filename pattern
    :param str _ref_units: The time units to be used as reference for the simulation
    :param str _ref_calendar: The time calendar  to be used as reference for the simulation
    :param boolean _write: Unable write mode if True
    :param boolean _force: Force write mode if True
    :param boolean _on_fly: Disable some check if True for incomplete time axis
    :param multiprocessing.Lock _lock: Lock to ensure only one process print to std_out at a time
    """
    global pattern, ref_units, ref_calendar, write, force, on_fly, lock
    pattern = _pattern
    ref_units = _ref_units
    ref_calendar = _ref_calendar
    write = _write
    force = _force
    on_fly = _on_fly
    lock = _lock


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
        # Init processes pool
        std_out_lock = Lock()
        pool = Pool(processes=ctx.processes, initializer=process_context, initargs=(ctx.pattern,
                                                                                    ctx.tinit.tunits,
                                                                                    ctx.tinit.calendar,
                                                                                    ctx.write,
                                                                                    ctx.force,
                                                                                    ctx.on_fly,
                                                                                    std_out_lock))
        # Process supplied files
        handlers = [x for x in pool.imap(process, ctx.sources)]
        # Close pool of workers
        pool.close()
        pool.join()
        ctx.scan_files = len(handlers)
