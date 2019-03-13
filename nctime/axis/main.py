#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Rewrite and/or check time axis of MIP NetCDF files.

"""

import itertools
import traceback
from multiprocessing import Pool

import numpy as np

from constants import *
from context import ProcessingContext
from handler import File
from nctime.utils.custom_print import *
from nctime.utils.misc import ProcessContext
from nctime.utils.time import trunc, truncated_timestamp, str2dates


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
                  input_start_timestamp=pctx.ref_start,
                  input_end_timestamp=pctx.ref_end)
        # Check time axis correctness
        wrong_timesteps = list()
        # Rebuild a theoretical time axis with appropriate precision
        fh.time_axis_rebuilt = trunc(fh.build_time_axis(), NDECIMALS)
        if not np.array_equal(fh.time_axis_rebuilt, fh.time_axis):
            fh.status.append(ERROR_TIME_AXIS_KO)
            time_axis_diff = (fh.time_axis_rebuilt == fh.time_axis)
            wrong_timesteps = list(np.where(time_axis_diff == False)[0])
        # Check time boundaries correctness
        wrong_bounds = list()
        if fh.has_bounds:
            fh.time_bounds_rebuilt = trunc(fh.build_time_bounds(), NDECIMALS)
            if not np.array_equal(fh.time_bounds_rebuilt, fh.time_bounds):
                fh.status.append(ERROR_TIME_BOUNDS_KO)
                time_bounds_diff = (fh.time_bounds_rebuilt == fh.time_bounds)
                wrong_bounds = list(np.where(np.all(time_bounds_diff, axis=1) == False)[0])
        # Get last theoretical date
        fh.last_num = fh.time_axis_rebuilt[-1]
        fh.last_date = fh.date_axis_rebuilt[-1]
        fh.last_timestamp = truncated_timestamp(str2dates(fh.last_date), fh.timestamp_length)
        # Check consistency between start date infile and start date from filename
        if fh.start_date_infile != fh.start_date_filename:
            if fh.start_date_infile < fh.start_date_filename:
                fh.status.append(ERROR_START_DATE_IN_VS_NAME)
            else:
                fh.status.append(ERROR_START_DATE_NAME_VS_IN)
        # Check consistency between end date infile and end date from filename
        if not pctx.on_fly and fh.end_date_infile != fh.end_date_filename:
            if fh.end_date_infile < fh.end_date_filename:
                fh.status.append(ERROR_END_DATE_IN_VS_NAME)
            else:
                fh.status.append(ERROR_END_DATE_NAME_VS_IN)
        # Check consistency between rebuilt end date and end date from filename
        if not pctx.on_fly and fh.last_date != fh.end_date_filename:
            if fh.last_date < fh.end_date_filename:
                fh.status.append(ERROR_END_DATE_REF_VS_NAME)
            else:
                fh.status.append(ERROR_END_DATE_NAME_VS_REF)
        # Check consistency between rebuilt end date and end date infile
        if not pctx.on_fly and fh.last_date != fh.end_date_infile:
            if fh.last_date < fh.end_date_infile:
                fh.status.append(ERROR_END_DATE_REF_VS_IN)
            else:
                fh.status.append(ERROR_END_DATE_IN_VS_REF)
        # Check file consistency between instant time and time boundaries
        if fh.is_instant and fh.has_bounds:
            fh.status.append(ERROR_TIME_BOUNDS_INS)
        # Check file consistency between averaged time and time boundaries
        if not fh.is_instant and not fh.has_bounds:
            fh.status.append(ERROR_TIME_BOUNDS_AVE)
        # Check time units consistency between file and ref
        if pctx.ref_units != fh.tunits:
            fh.status.append(ERROR_TIME_UNITS)
        # Check calendar consistency between file and ref
        if pctx.ref_calendar != fh.calendar:
            fh.status.append(ERROR_TIME_CALENDAR)
        # Exclude codes to ignore from status codes
        # Before correction to avoid undesired operations
        fh.status = [code for code in fh.status if code not in pctx.ignore_codes]
        correction = False
        # Rename file depending on checking
        if (pctx.write and (
                (
                        ({ERROR_END_DATE_NAME_VS_IN, ERROR_END_DATE_IN_VS_NAME}.intersection(set(fh.status)))
                        and
                        {ERROR_END_DATE_NAME_VS_REF, ERROR_END_DATE_REF_VS_NAME}.intersection(set(fh.status))
                )
                or
                (
                        ({ERROR_END_DATE_NAME_VS_REF, ERROR_END_DATE_REF_VS_NAME}.intersection(set(fh.status))
                         and
                         {ERROR_END_DATE_IN_VS_REF, ERROR_END_DATE_REF_VS_IN}.intersection(set(fh.status)))
                )
        )) or pctx.force:
            # Change filename and file full path dynamically
            fh.nc_file_rename(new_filename=re.sub(fh.end_timestamp_filename, fh.last_timestamp, fh.filename))
            correction = True
        # Remove time boundaries depending on checking
        if pctx.write and ERROR_TIME_BOUNDS_INS in fh.status:
            # Delete time bounds and bounds attribute from file if write or force mode
            fh.nc_var_delete(variable=fh.tbnds)
            fh.nc_att_delete(attribute='bounds', variable='time')
            correction = True
        # Rewrite time units depending on checking
        if pctx.write and ERROR_TIME_UNITS in fh.status:
            fh.nc_att_overwrite('units', variable='time', data=pctx.ref_units)
        # Rewrite time calendar depending on checking
        if pctx.write and ERROR_TIME_CALENDAR in fh.status:
            fh.nc_att_overwrite('calendar', variable='time', data=pctx.ref_calendar)
        # Rewrite time axis depending on checking
        if (pctx.write and {ERROR_TIME_AXIS_KO, ERROR_TIME_BOUNDS_KO}.intersection(set(fh.status))) or pctx.force:
            fh.nc_var_overwrite('time', fh.time_axis_rebuilt)
            # Rewrite time boundaries if needed
            if fh.has_bounds:
                fh.nc_var_overwrite(fh.tbnds, fh.time_bounds_rebuilt)
            correction = True
        # Diagnostic display
        msgval = {}
        msgval['file'] = COLORS.HEADER(fh.filename)
        if ERROR_TIME_UNITS in fh.status:
            msgval['infile_units'] = COLORS.FAIL(fh.tunits)
            msgval['ref_units'] = COLORS.SUCCESS(pctx.ref_units)
        else:
            msgval['infile_units'] = COLORS.SUCCESS(fh.tunits)
            msgval['ref_units'] = COLOR('cyan').bold(pctx.ref_units)
        if ERROR_TIME_CALENDAR in fh.status:
            msgval['infile_calendar'] = COLORS.FAIL(fh.calendar)
            msgval['ref_calendar'] = COLORS.SUCCESS(pctx.ref_calendar)
        else:
            msgval['infile_calendar'] = COLORS.SUCCESS(fh.calendar)
            msgval['ref_calendar'] = COLOR('cyan').bold(pctx.ref_calendar)
        if {ERROR_START_DATE_IN_VS_NAME, ERROR_START_DATE_NAME_VS_IN}.intersection(set(fh.status)):
            msgval['infile_start_timestamp'] = COLORS.FAIL(fh.start_timestamp_infile)
            msgval['infile_start_date'] = COLORS.FAIL(fh.start_date_infile)
            msgval['infile_start_num'] = COLORS.FAIL(str(fh.start_num_infile))
            msgval['ref_start_timestamp'] = COLORS.SUCCESS(fh.start_timestamp_filename)
            msgval['ref_start_date'] = COLORS.SUCCESS(fh.start_date_filename)
            msgval['ref_start_num'] = COLORS.SUCCESS(str(fh.start_num_filename))
        else:
            msgval['infile_start_timestamp'] = COLORS.SUCCESS(fh.start_timestamp_infile)
            msgval['infile_start_date'] = COLORS.SUCCESS(fh.start_date_infile)
            msgval['infile_start_num'] = COLORS.SUCCESS(str(fh.start_num_infile))
            msgval['ref_start_timestamp'] = COLOR('cyan').bold(fh.start_timestamp_filename)
            msgval['ref_start_date'] = COLOR('cyan').bold(fh.start_date_filename)
            msgval['ref_start_num'] = COLOR('cyan').bold(str(fh.start_num_filename))
        if {ERROR_END_DATE_NAME_VS_REF, ERROR_END_DATE_REF_VS_NAME}.intersection(set(fh.status)):
            msgval['filename_end_timestamp'] = COLORS.FAIL(fh.end_timestamp_filename)
            msgval['filename_end_date'] = COLORS.FAIL(fh.end_date_filename)
            msgval['filename_end_num'] = COLORS.FAIL(str(fh.end_num_filename))
        else:
            msgval['filename_end_timestamp'] = COLORS.SUCCESS(fh.end_timestamp_filename)
            msgval['filename_end_date'] = COLORS.SUCCESS(fh.end_date_filename)
            msgval['filename_end_num'] = COLORS.SUCCESS(str(fh.end_num_filename))
        if {ERROR_END_DATE_IN_VS_REF, ERROR_END_DATE_REF_VS_IN}.intersection(set(fh.status)):
            msgval['infile_end_timestamp'] = COLORS.FAIL(fh.end_timestamp_infile)
            msgval['infile_end_date'] = COLORS.FAIL(fh.end_date_infile)
            msgval['infile_end_num'] = COLORS.FAIL(str(fh.end_num_infile))
        else:
            msgval['infile_end_timestamp'] = COLORS.SUCCESS(fh.end_timestamp_infile)
            msgval['infile_end_date'] = COLORS.SUCCESS(fh.end_date_infile)
            msgval['infile_end_num'] = COLORS.SUCCESS(str(fh.end_num_infile))
        msgval['ref_end_timestamp'] = COLOR('cyan').bold(fh.last_timestamp)
        msgval['ref_end_date'] = COLOR('cyan').bold(fh.last_date)
        msgval['ref_end_num'] = COLOR('cyan').bold(str(fh.last_num))
        msgval['len'] = fh.length
        msgval['table'] = fh.table
        msgval['freq'] = fh.frequency
        msgval['step'] = fh.step
        msgval['units'] = fh.step_units
        msgval['instant'] = fh.is_instant
        msgval['clim'] = fh.is_climatology
        msgval['bnds'] = fh.has_bounds

        msg = """{file}
        Units:
            IN FILE -- {infile_units}
            REF     -- {ref_units}
        Calendar:
            IN FILE -- {infile_calendar}
            REF     -- {ref_calendar}
        Start: 
            IN FILE -- {infile_start_timestamp} = {infile_start_date} = {infile_start_num}
            REF     -- {ref_start_timestamp} = {ref_start_date} = {ref_start_num}
        End:
            FILENAME -- {filename_end_timestamp} = {filename_end_date} = {filename_end_num}
            IN FILE  -- {infile_end_timestamp} = {infile_end_date} = {infile_end_num}
            REBUILT  -- {ref_end_timestamp} = {ref_end_date} = {ref_end_num}
        Length: {len}
        MIP table: {table}
        Frequency: {freq} = {step} {units}
        Is instant: {instant}
        Is climatology: {clim}
        Has bounds: {bnds}""".format(**msgval)

        # Add status message
        if fh.status:
            for s in fh.status:
                msg += """\n        Status: {} """.format(COLORS.FAIL('Error {} -- {}'.format(s, STATUS[s])))
                if correction and s in ERROR_CORRECTED_SET:
                    msg += ' -- {}'.format(COLORS.SUCCESS('Corrected'))
        else:
            msg += """\n        Status: {}""".format(COLORS.SUCCESS(STATUS[ERROR_TIME_AXIS_OK]))
        # Display wrong time steps and/or bounds
        timestep_limit = pctx.limit if pctx.limit else len(wrong_timesteps)
        for i, v in enumerate(wrong_timesteps):
            if (i + 1) <= timestep_limit:
                msg += """\n        Wrong time step at index {}: IN FILE -- {} = {} vs. REBUILT -- {} = {}""".format(
                    COLORS.HEADER(str(v + 1)),
                    COLORS.FAIL(fh.date_axis[v]),
                    COLORS.FAIL(str(fh.time_axis[v]).ljust(10)),
                    COLORS.SUCCESS(fh.date_axis_rebuilt[v]),
                    COLORS.SUCCESS(str(fh.time_axis_rebuilt[v]).ljust(10)))
        bounds_limit = pctx.limit if pctx.limit else len(wrong_bounds)
        for i, v in enumerate(wrong_bounds):
            if (i + 1) <= bounds_limit:
                msg += """\n        Wrong time bounds at index {}: IN FILE -- {} = {} vs. REBUILT -- {} = {}""".format(
                    COLORS.HEADER(str(v + 1)),
                    COLORS.FAIL('[{} {}]'.format(fh.date_bounds[v][0], fh.date_bounds[v][1])),
                    COLORS.FAIL(str(fh.time_bounds[v]).ljust(20)),
                    COLORS.SUCCESS('[{} {}]'.format(fh.date_bounds_rebuilt[v][0], fh.date_bounds_rebuilt[v][1])),
                    COLORS.SUCCESS(str(fh.time_bounds_rebuilt[v]).ljust(20)))
        # Acquire lock to print result
        with pctx.lock:
            if fh.status:
                Print.error(msg, buffer=True)
            else:
                Print.success(msg, buffer=True)
        # Return error if it is the case
        if fh.status:
            return 1
        else:
            return 0
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = COLORS.HEADER('{}'.format(os.path.basename(ffp)))
        msg += """\n        Status: {}""".format(COLORS.FAIL('Skipped'))
        msg += """\n        {}""".format(exc[0])
        msg += """\n      """
        msg += """\n      """.join(exc[1:])
        with pctx.lock:
            Print.error(msg, buffer=True)
        return None
    finally:
        # Print progress
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbfiles)
            msg = COLORS.OKBLUE('\rProcess netCDF file(s): ')
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
            locals()['pool'].terminate()
        Print.progress('\n')
        # Flush buffer
        Print.flush()
        # Get number of errors
        ctx.nbskip = ctx.nbfiles - len(handlers)
        ctx.nberrors = sum(handlers)
    # Evaluate errors and exit with appropriate return code
    if ctx.nbskip or ctx.nberrors:
        sys.exit(ctx.nbskip + ctx.nberrors)
