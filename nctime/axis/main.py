#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import logging
import re
import sys
from multiprocessing import Pool, Lock

import numpy as np

from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.misc import trunc, COLORS


def process(ffp):
    """
    Process time axis checkup and rewriting if needed.

    :param str ffp: The file full path to process
    :returns: The file status
    :rtype: *list*

    """
    # Declare variables from initializer to avoid IDE warnings
    global pattern, ref_units, ref_calendar, true_dates, write, force, limit, ignore_codes, lock, on_fly
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp=ffp,
                  pattern=pattern,
                  ref_units=ref_units,
                  ref_calendar=ref_calendar,
                  true_dates=true_dates)
        fh.load_last_date()
        # In the case of inconsistent timestamps, it may be due to float precision issue
        if not on_fly and fh.last_timestamp != fh.end_timestamp:
            fh.start_num = trunc(fh.start_num, 5)
            fh.load_last_date()
            if fh.last_timestamp != fh.end_timestamp:
                fh.status.append('003')
        # Check consistency between last time date and end date from filename
        if not on_fly and fh.last_date != fh.end_date:
            fh.status.append('008')
        # Check file consistency between instant time and time boundaries
        if fh.is_instant and fh.has_bounds:
            fh.status.append('004')
        # Check file consistency between averaged time and time boundaries
        if not fh.is_instant and not fh.has_bounds:
            fh.status.append('005')
        # Check time axis squareness
        wrong_timesteps = list()
        if not {'003', '008'}.intersection(set(fh.status)):
            # Rebuild a theoretical time axis with appropriate precision
            fh.time_axis_rebuilt = fh.build_time_axis()
            if not np.array_equal(fh.time_axis_rebuilt, fh.time_axis):
                fh.status.append('001')
                time_axis_diff = (fh.time_axis_rebuilt == fh.time_axis)
                wrong_timesteps = list(np.where(time_axis_diff == False)[0])
        # Check time boundaries squareness
        wrong_bounds = list()
        if fh.has_bounds and '004' not in fh.status:
            fh.time_bounds_rebuilt = fh.build_time_bounds()
            if not np.array_equal(fh.time_bounds_rebuilt, fh.time_bounds):
                fh.status.append('006')
                time_bounds_diff = (fh.time_bounds_rebuilt == fh.time_bounds)
                wrong_bounds = list(np.where(np.all(time_bounds_diff, axis=1) == False)[0])
        # Check time units consistency between file and ref
        if ref_units != fh.tunits:
            fh.status.append('002')
        # Check calendar consistency between file and ref
        if ref_calendar != fh.calendar:
            fh.status.append('007')
        # Rename file depending on checking
        if (write and {'003'}.intersection(set(fh.status))) or force:
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp, fh.last_timestamp, fh.filename))
        # Remove time boundaries depending on checking
        if (write and {'004'}.intersection(set(fh.status))) or force:
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
        # Diagnostic display
        msg = """{}
        Units: {} [ref = {}]
        Calendar: {} [ref = {}]
        Start: {} = {} = {}
        End:   {} = {} = {}
        Last:  {} = {} = {}
        Length: {}
        Frequency: {} = {} {}
        Is instant: {}
        Has bounds: {}""".format(COLORS.HEADER + fh.filename + COLORS.ENDC,
                                 fh.tunits, ref_units,
                                 fh.calendar, ref_calendar,
                                 fh.start_timestamp, fh.start_date, fh.start_num,
                                 fh.end_timestamp, fh.end_date, fh.end_num,
                                 fh.last_timestamp, fh.last_date, fh.last_num,
                                 fh.length,
                                 fh.frequency, fh.step, fh.step_units,
                                 fh.is_instant,
                                 fh.has_bounds)
        if fh.status:
            for s in fh.status:
                if s in ignore_codes:
                    msg += """\n        Status: {}""".format(COLORS.FAIL + STATUS[s] + COLORS.ENDC)
        else:
            msg += """\n        Status: {}""".format(COLORS.OKGREEN + STATUS['000'] + COLORS.ENDC)
        # Display wrong time steps and/or bounds
        timestep_limit = limit if limit else len(wrong_timesteps)
        for i, v in enumerate(wrong_timesteps):
            if (i + 1) <= timestep_limit:
                msg += """\n        Wrong timestep: {} iso {}""".format(str(fh.time_axis[v]).ljust(10),
                                                                        str(fh.time_axis_rebuilt[v]).ljust(10))
        bounds_limit = limit if limit else len(wrong_bounds)
        for i, v in enumerate(wrong_bounds):
            if (i + 1) <= bounds_limit:
                msg += """\n        Wrong bound: {} iso {}""".format(str(fh.time_bounds[v]).ljust(10),
                                                                     str(fh.time_bounds_rebuilt[v]).ljust(10))
        # Acquire lock to standard output
        lock.acquire()
        if fh.status:
            logging.error(msg)
        else:
            logging.info(msg)
        # Release lock on standard output
        lock.release()
        # Return error if it is the case
        if fh.status:
            return 1
        else:
            return 0
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return 1


def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    :param list keys: Argument name list
    :param list values: Argument value list

    """
    assert len(keys) == len(values)
    for i, key in enumerate(keys):
        globals()[key] = values[i]


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
        # Init process context
        ProcessContext = {name: getattr(ctx, name) for name in PROCESS_VARS}
        ProcessContext['lock'] = Lock()
        # Init processes pool
        pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(ProcessContext.keys(),
                                                                                ProcessContext.values()))
        # Process supplied files
        handlers = [x for x in pool.imap(process, ctx.sources)]
        # Close pool of workers
        pool.close()
        pool.join()
        ctx.scan_errors = sum(handlers)
        ctx.scan_files = len(handlers)
    # Exist status if scan errors
    if ctx.scan_errors:
        sys.exit(1)
