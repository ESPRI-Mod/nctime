#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import itertools
import os
import re
import sys
import traceback
from multiprocessing import Pool

import numpy as np

from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.misc import trunc, COLORS, ProcessContext, Print
from nctime.utils.time import trunc


def process(ffp):
    """
    Process time axis checkup and rewriting if needed.

    :param str ffp: The file full path to process
    :returns: The file status
    :rtype: *list*

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp=ffp,
                  pattern=pctx.pattern,
                  ref_units=pctx.ref_units,
                  ref_calendar=pctx.ref_calendar,
                  correction=pctx.correction)
        fh.load_last_date()
        # In the case of inconsistent timestamps, it may be due to float precision issue
        if not pctx.on_fly and fh.last_timestamp != fh.end_timestamp:
            if int(float(fh.last_timestamp)) < int(float(fh.end_timestamp)):
                fh.status.append('003a')
            else:
                fh.status.append('003b')
        # Check consistency between last time date and end date from filename
        if not pctx.on_fly and fh.last_date != fh.end_date:
            if fh.last_date < fh.end_date:
                fh.status.append('008a')
            else:
                fh.status.append('008b')
        # Check file consistency between instant time and time boundaries
        if fh.is_instant and fh.has_bounds:
            fh.status.append('004')
        # Check file consistency between averaged time and time boundaries
        if not fh.is_instant and not fh.has_bounds:
            fh.status.append('005')
        # Check time axis squareness
        wrong_timesteps = list()
        # Rebuild a theoretical time axis with appropriate precision
        fh.time_axis_rebuilt = trunc(fh.build_time_axis(), NDECIMALS)
        if not np.array_equal(fh.time_axis_rebuilt, fh.time_axis):
            fh.status.append('001')
            time_axis_diff = (fh.time_axis_rebuilt == fh.time_axis)
            wrong_timesteps = list(np.where(time_axis_diff == False)[0])
        # Check time boundaries squareness
        wrong_bounds = list()
        if fh.has_bounds and not {'004'}.intersection(set(fh.status)):
            fh.time_bounds_rebuilt = trunc(fh.build_time_bounds(), NDECIMALS)
            if not np.array_equal(fh.time_bounds_rebuilt, fh.time_bounds):
                fh.status.append('006')
                time_bounds_diff = (fh.time_bounds_rebuilt == fh.time_bounds)
                wrong_bounds = list(np.where(np.all(time_bounds_diff, axis=1) == False)[0])
        # Check time units consistency between file and ref
        if pctx.ref_units != fh.tunits:
            fh.status.append('002')
        # Check calendar consistency between file and ref
        if pctx.ref_calendar != fh.calendar:
            fh.status.append('007')
        # Rename file depending on checking
        if (pctx.write and {'003'}.intersection(set(fh.status))) or pctx.force:
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp, fh.last_timestamp, fh.filename))
        # Remove time boundaries depending on checking
        if (pctx.write and {'004'}.intersection(set(fh.status))) or pctx.force:
            # Delete time bounds and bounds attribute from file if write or force mode
            fh.nc_var_delete(variable=fh.tbnds)
            fh.nc_att_delete(attribute='bounds', variable='time')
        # Rewrite time axis depending on checking
        if (pctx.write and {'001', '002', '006', '007'}.intersection(set(fh.status))) or pctx.force:
            fh.nc_var_overwrite('time', fh.time_axis_rebuilt)
            fh.nc_att_overwrite('units', 'time', pctx.ref_units)
            fh.nc_att_overwrite('calendar', 'time', pctx.ref_calendar)
            # Rewrite time boundaries if needed
            if fh.has_bounds:
                fh.nc_var_overwrite('time_bounds', fh.time_bounds_rebuilt)
        # Diagnostic display
        msg = """\n{}
        Units: {} [ref = {}]
        Calendar: {} [ref = {}]
        Start: {} = {} = {}
        End:   {} = {} = {}
        Last:  {} = {} = {}
        Length: {}
        Frequency: {} = {} {}
        Is instant: {}
        Has bounds: {}""".format(COLORS.HEADER + fh.filename + COLORS.ENDC,
                                 fh.tunits, pctx.ref_units,
                                 fh.calendar, pctx.ref_calendar,
                                 fh.start_timestamp, fh.start_date, fh.start_num,
                                 fh.end_timestamp, fh.end_date, fh.end_num,
                                 fh.last_timestamp, fh.last_date, fh.last_num,
                                 fh.length,
                                 fh.frequency, fh.step, fh.step_units,
                                 fh.is_instant,
                                 fh.has_bounds)
        # Exclude codes to ignore from status codes
        fh.status = [code for code in fh.status if code not in pctx.ignore_codes]
        # Add status message
        if fh.status:
            for s in fh.status:
                msg += """\n        Status: {} """.format(COLORS.FAIL + 'Error ' + s + ' -- ' + STATUS[s] + COLORS.ENDC)
        else:
            msg += """\n        Status: {}""".format(COLORS.OKGREEN + STATUS['000'] + COLORS.ENDC)
        # Display wrong time steps and/or bounds
        timestep_limit = pctx.limit if pctx.limit else len(wrong_timesteps)
        for i, v in enumerate(wrong_timesteps):
            if (i + 1) <= timestep_limit:
                msg += """\n        Wrong timestep: {} iso {}""".format(str(fh.time_axis[v]).ljust(10),
                                                                        str(fh.time_axis_rebuilt[v]).ljust(10))
        bounds_limit = pctx.limit if pctx.limit else len(wrong_bounds)
        for i, v in enumerate(wrong_bounds):
            if (i + 1) <= bounds_limit:
                msg += """\n        Wrong bound: {} iso {}""".format(str(fh.time_bounds[v]).ljust(10),
                                                                     str(fh.time_bounds_rebuilt[v]).ljust(10))
        # Acquire lock to print result
        pctx.lock.acquire()
        if fh.status:
            Print.error(msg, buffer=True)
        else:
            Print.success(msg, buffer=True)
        # Release lock
        pctx.lock.release()
        # Return error if it is the case
        if fh.status:
            return 1
        else:
            return 0
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = COLORS.HEADER + '\n{}'.format(os.path.basename(ffp)) + COLORS.ENDC
        msg += """\n        Status: {}""".format(COLORS.FAIL + 'Skipped' + COLORS.ENDC)
        msg += """\n        {}""".format(exc[0])
        msg += """\n      """
        msg += """\n      """.join(exc[1:-1])
        msg += COLORS.FAIL + """\n        {}""".format(exc[-1]) + COLORS.ENDC
        Print.error(msg, buffer=True)
        return None
    finally:
        # Print progress
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbfiles)
            msg = COLORS.OKGREEN + '\rProcess netCDF file(s): ' + COLORS.ENDC
            msg += '{}% | {}/{} files'.format(percentage, pctx.progress.value, pctx.nbfiles)
            Print.progress(msg)


def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    :param list keys: Argument name list
    :param list values: Argument value list

    """
    assert len(keys) == len(values)
    global pctx
    pctx = ProcessContext({key: values[i] for i, key in enumerate(keys)})


def run(args=None):
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
        # Init print management
        Print.init(log=args.log, debug=args.debug, all=args.all, cmd='{}-{}'.format(args.prog, args.cmd))
        # Print command-line
        Print.command(COLORS.OKBLUE + 'Command: ' + COLORS.ENDC + ' '.join(sys.argv) + '\n')
        # Collecting data
        Print.progress('\rAnalysing data, please wait...')
        ctx.nbfiles = len(ctx.sources)
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        if ctx.use_pool:
            # Init processes pool
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))
            # Process supplied files
            processes = pool.imap(process, ctx.sources)
        else:
            initializer(cctx.keys(), cctx.values())
            processes = itertools.imap(process, ctx.sources)
        # Process supplied sources
        handlers = [x for x in processes if x is not None]
        # Close pool of workers if exists
        if 'pool' in locals().keys():
            locals()['pool'].close()
            locals()['pool'].join()
        # Flush buffer
        Print.flush()
        # Get number of errors
        ctx.nbskip = ctx.nbfiles - len(handlers)
        ctx.nberrors = sum(handlers)
    # Evaluate errors and exit with appropriate return code
    if ctx.nbskip or ctx.nberrors:
        if (ctx.nbskip + ctx.nberrors) == ctx.nbfiles:
            # All files has error(s). Error code = -1
            sys.exit(2)
        else:
            # Some files (at least one) has error(s). Error code = nb files with error(s)
            sys.exit(1)
    else:
        # No errors. Error code = 0
        sys.exit(0)


if __name__ == "__main__":
    run()
