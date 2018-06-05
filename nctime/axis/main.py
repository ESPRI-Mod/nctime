#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import itertools
import logging
import re
import sys
from time import sleep
from multiprocessing import Pool, Lock

import numpy as np

from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.misc import trunc, COLORS, ProcessContext


def process(ffp):
    """
    Process time axis checkup and rewriting if needed.

    :param str ffp: The file full path to process
    :returns: The file status
    :rtype: *list*

    """
    # Declare context from initializer to avoid IDE warnings
    global cctx
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp=ffp,
                  pattern=cctx.pattern,
                  ref_units=cctx.ref_units,
                  ref_calendar=cctx.ref_calendar,
                  correction=cctx.correction)
        fh.load_last_date()
        # In the case of inconsistent timestamps, it may be due to float precision issue
        if not cctx.on_fly and fh.last_timestamp != fh.end_timestamp:
            fh.start_num = trunc(fh.start_num, 5)
            fh.load_last_date()
            if fh.last_timestamp != fh.end_timestamp:
                fh.status.append('003')
        # Check consistency between last time date and end date from filename
        if not cctx.on_fly and fh.last_date != fh.end_date:
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
        if fh.has_bounds and not {'003', '008', '004'}.intersection(set(fh.status)):
            fh.time_bounds_rebuilt = fh.build_time_bounds()
            if not np.array_equal(fh.time_bounds_rebuilt, fh.time_bounds):
                fh.status.append('006')
                time_bounds_diff = (fh.time_bounds_rebuilt == fh.time_bounds)
                wrong_bounds = list(np.where(np.all(time_bounds_diff, axis=1) == False)[0])
        # Check time units consistency between file and ref
        if cctx.ref_units != fh.tunits:
            fh.status.append('002')
        # Check calendar consistency between file and ref
        if cctx.ref_calendar != fh.calendar:
            fh.status.append('007')
        # Rename file depending on checking
        if (cctx.write and {'003'}.intersection(set(fh.status))) or cctx.force:
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp, fh.last_timestamp, fh.filename))
        # Remove time boundaries depending on checking
        if (cctx.write and {'004'}.intersection(set(fh.status))) or cctx.force:
            # Delete time bounds and bounds attribute from file if write or force mode
            fh.nc_var_delete(variable=fh.tbnds)
            fh.nc_att_delete(attribute='bounds', variable='time')
        # Rewrite time axis depending on checking
        if (cctx.write and {'001', '002', '006', '007'}.intersection(set(fh.status))) or cctx.force:
            fh.nc_var_overwrite('time', fh.time_axis_rebuilt)
            fh.nc_att_overwrite('units', 'time', cctx.ref_units)
            fh.nc_att_overwrite('calendar', 'time', cctx.ref_calendar)
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
                                 fh.tunits, cctx.ref_units,
                                 fh.calendar, cctx.ref_calendar,
                                 fh.start_timestamp, fh.start_date, fh.start_num,
                                 fh.end_timestamp, fh.end_date, fh.end_num,
                                 fh.last_timestamp, fh.last_date, fh.last_num,
                                 fh.length,
                                 fh.frequency, fh.step, fh.step_units,
                                 fh.is_instant,
                                 fh.has_bounds)
        # Exclude codes to ignore from status codes
        fh.status = [code for code in fh.status if code not in cctx.ignore_codes]
        # Add status message
        if fh.status:
            for s in fh.status:
                msg += """\n        Status: {} """.format(COLORS.FAIL + 'Error ' + s + ' -- ' + STATUS[s] + COLORS.ENDC)
        else:
            msg += """\n        Status: {}""".format(COLORS.OKGREEN + STATUS['000'] + COLORS.ENDC)
        # Display wrong time steps and/or bounds
        timestep_limit = cctx.limit if cctx.limit else len(wrong_timesteps)
        for i, v in enumerate(wrong_timesteps):
            if (i + 1) <= timestep_limit:
                msg += """\n        Wrong timestep: {} iso {}""".format(str(fh.time_axis[v]).ljust(10),
                                                                        str(fh.time_axis_rebuilt[v]).ljust(10))
        bounds_limit = cctx.limit if cctx.limit else len(wrong_bounds)
        for i, v in enumerate(wrong_bounds):
            if (i + 1) <= bounds_limit:
                msg += """\n        Wrong bound: {} iso {}""".format(str(fh.time_bounds[v]).ljust(10),
                                                                     str(fh.time_bounds_rebuilt[v]).ljust(10))
        # Acquire lock to print result
        cctx.lock.acquire()
        if fh.status:
            logging.error(msg)
        else:
            logging.info(msg)
        # Release lock
        cctx.lock.release()
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
    global cctx
    cctx = ProcessContext({key: values[i] for i, key in enumerate(keys)})


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
        # Critical level used to print in any case
        logging.critical('Command: ' + ' '.join(sys.argv))
        sleep(0.1)
        print("Analysing data, please wait...\r")
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        cctx['lock'] = Lock()
        if ctx.use_pool:
            # Init processes pool
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))
            # Process supplied files
            handlers = [x for x in pool.imap(process, ctx.sources)]
            # Close pool of workers
            pool.close()
            pool.join()
        else:
            initializer(cctx.keys(), cctx.values())
            handlers = [x for x in itertools.imap(process, ctx.sources)]
        ctx.scan_errors = sum(handlers)
        ctx.scan_files = len(handlers)
    # Exist status if scan errors
    if ctx.scan_errors:
        sys.exit(1)
    # Evaluate errors and exit with appropriate return code
    if ctx.scan_errors:
        if ctx.scan_errors == ctx.scan_files:
            # All files has error(s). Error code = -1
            sys.exit(-1)
        else:
            # Some files (at least one) has error(s). Error code = nb files with error(s)
            sys.exit(ctx.scan_files)
    else:
        # No errors. Error code = 0
        sys.exit(0)
