.. _faq:

Frequently asked questions
==========================


What ``nctime overlap`` does?
*****************************

The ``nctime overlap`` finds gaps or overlaps between the time samples contained in a dataset split across files.
It is only based on the timestamps from filenames, the time axis is never read in this context.
Basically, it tries to find the shorted path from the start date to the end date of the period. If no path is found, some breaks appears in the time series.
If a path is found among the nodes, the nodes put a side are the overlapping files.

How ``nctime`` detects gaps or overlaps in a time series?
*********************************************************

The ``nctime overlap`` code uses the `networkx <https://networkx.github.io/>`_ Python library to build a directed graph of nodes.
Each node corresponds to a file described by:

 * the first timestamp of the filename
 * the last timestamp of the filename
 * the next expected timestamps depending on inputs:
    * the time frequency from the global attributes of the file.
    * the base time units from the time attribute of the FIRST file scanned. Can be enforced using ``--units`` flag.
    * the time calendar from the time attribute of the FIRST file scanned. Ca be enforced using ``--calendar`` flag.

Such a graph is built for each dataset split across files. This means a graph per dataset. each graph is then parsed to find the shortest path from the earlier timestamp to the latest one.
The code uses the unweighted `shortest_path <https://networkx.github.io/documentation/stable/reference/algorithms/shortest_paths.html>`_ method.

If no path found, the code analyzes the different nodes to detect the breaks in the time series.
Those breaks must be manually fill to solve the error.

If a path is found, the code returns the unused nodes. This means that the corresponding files are unecessary to cover the whole time period and could be removed.
The code is also able to detect partial overlap. This occurs when a subperiod is included in two files. In the case only, the code reads the time axis of both files to catch the timestep to cut in order to resolve the overlap.
In case of overlapping files, you can use the ``--write`` flag to automatically solve the overlaps. Be careful partial overlaps can be quite long to resolve as they require to create new files on disk.

How to interpret file diagnostics from ``nctime overlap``?
**********************************************************

After processing all files, ``overlap`` prints the result of each graph parsed with the following layout:

.. code-block:: text

  [Time series status]
    [File #1]
    [File #2]
    [File #3]
    [...]

Overlaps will be indicated as follows:

.. code-block:: text

  [Time series status]
    [File #1]
    [File #2] <-- to remove
    [File #3] <-- overlaps from YYYYMMDDHHmmss to YYYYMMDDHHmmss
    [...]

Broken time series will be indicated as follows:

.. code-block:: text

  [Time series status]
    [File #1]
     BREAK
    [File #3]
    [...]

What ``nctime axis`` does?
*****************************

The ``nctime axis`` code analyzes the time coordinate only (not other coordinates). It also checks the time boundaries
if exists and some time attributes as the calendar and the base time units.
Basically, the code rebuilt a theoretical time axis depending on inputs:

 * the time frequency from the global attributes of each netCDF file.
 * the base time units from the time attribute of the FIRST file scanned. Can be enforced using ``--units`` flag.
 * the time calendar from the time attribute of the FIRST file scanned. Can be enforced using ``--calendar`` flag
 * the first timestamps from each filename. Can be enforced using ``--start`` flag

Then, the theoretical time axis is compared to the infile time axis. If exist, the differences between theoretical and infile axes are categorized with different error codes.

How ``nctime`` checks the time coordinate?
******************************************

The ``nctime axis `` uses the `netcdftime <https://www.esrl.noaa.gov/psd/people/jeffrey.s.whitaker/python/netcdftime.html>`_ package part of the ``netCDF4`` Python library. It rebuilds in a iterative way the theoretical time axis.
Its usual ``date2num`` and ``num2date`` methods have been extended to support all time units (including month and year).
In addition, an offset of +0.5 time step is applied to the rebuilt non-instant time axis.
A particular treatment is applied to climatology axis following `CF Conventions <http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#climatological-statistics>`_.

How to interpret file diagnostics from ``nctime axis``?
*******************************************************

First of all, ``axis`` print useful information for each file scanned with the following layout.

.. code-block:: text

  [FILENAME]
        Units:
            IN FILE -- [infile base time units in the format "days since YYYY-MM-DD HH:mm:ss]
            REF     -- [reference base time units in the format "days since YYYY-MM-DD HH:mm:ss]
        Calendar:
            IN FILE -- [infile time calendar]
            REF     -- [reference time calendar]
        Start:
            IN FILE -- [first timestamps from filename] = [first date from infile time axis in ISO format] = [corresponding number of days since infile base time units]
            REBUILT -- [first theoretical timestamps] = [first theoretical date in ISO format] = [corresponding number of days since ref base time units]
        End:
            IN FILE -- [end timestamps from filename] = [last date from infile time axis in ISO format] = [corresponding number of days since infile base time units]
            REBUILT -- [end theoretical timestamps] = [last theoretical date in ISO format] = [corresponding number of days since ref base time units]
        Length: [number of time steps]
        MIP table: [MIP table ID from netCDF global attributes]
        Frequency: [time frequency name] = [time frequency units]
        Is instant: [True/False]
        Is climatology: [True/False]
        Has bounds: [True/False]
        Status: [CODE(S)]

The file status can include one or several of the following error codes.

 * 000: No errors.
    * Infile time axis seems correct
    * No correction required.
 * 001: Infile axis seems to have one or several wrong time steps.
    * This error often comes along the error 006 (wrong time boundaries).
    * This error can be corrected with ``--write`` option in order to write the rebuilt theoretical time axis into the file itself without copying it.
 * 002: Time units must be unchanged for the same dataset
    * For a dataset split across files, the base time units needs to be the same (see CF Convention).
    * Broadly we recommend to set the same base time units and calendar for the whole simulation (including all frequencies and all variables).
    * This error can be corrected with ``--write`` option to replace infile attribute with the reference value (i.e., from first file scanned or the ``--units`` flag).
    * This error could be ignored if you're scanning more than one simulation at a time. In this case, different calendars could be expected.
 * 003: Last timestamp is lower than end timestamp from filename
    * The date of last theoretical time steps is lower than the end date from the filename.
    * Without any other errors it means that infile time axis is OK but the filename must be renamed by changing the last timestamps according to the diagnostic. In this case the error can be corrected by using the ``--write`` flag.
    * If associated to the error 001 at the first timesteps it means that the whole time axis is wrong probably due to a wrong first timestamp in the filename. In this case the error can be corrected by manually renaming the file with the appropriate first timestamp. Be careful to rerun ``axis`` diagnostic then to ensure that no other errors.
 * 004: An instantaneous time axis should not embed time boundaries
    * The data are described on an instantaneous time axis but the file includes time boundaries.
    * In such a case the time boundaries are useless.
    * You can choose the remove the tome boundaries using the ``--write``.
    * In any case the time boundaries are check according to the time axis. For instant time axis, the time boundaries, if kept, have to be, at least, a copy of the time axis to ensure equivalent time means.
 * 005: An averaged time axis should embed time boundaries
    * This is the opposite of the error 004. Time boundaries are missing in the case of a non-instant time axis.
    * This error can NOT be corrected using the ``--write`` flag.
    * Time boundaries must be append to the file manually.
 * 006: Incorrect time bounds over one or several time steps
    * The error is often associated to the error 001.
    * This error can be corrected with ``--write`` option in order to write the rebuilt theoretical time bounds into the file itself without copying it.
 * 007: Different calendars between files.
    * For a dataset split across files, the time calendar needs to be unchanged (see CF Convention).
    * Broadly we recommend to set the same base time units and calendar for the whole simulation (including all frequencies and all variables).
    * This error can be corrected with ``--write`` option to replace infile attribute with the reference value (i.e., from first file scanned or the ``--units`` flag).
    * This error could be ignored if you're scanning more than one simulation at a time. In this case, different calendars could be expected.
 * 008: Last timestamp is higher than end timestamp from filename
    * This is the opposite of the error 003.
    * This error can NOT be corrected using the ``--write`` flag because we cannot deduce if this is the filename or the time axis that is wrong.
    * This error must be solved manually by investigating the file.

Anyway, since you solved the errors on time axis, running ``axis`` a second time will provide a green flag.

Should we run ``nctime`` tools in a specific sequence?
******************************************************

Because ``overlap`` tool is ONLY based on the timestamps from the filenames, we recommend run ``axis`` tool before ``overlap``.
You must then rename filenames if needed depending on ``axis`` diagnostics. Then, the ``overlap`` result can be safety interpreted.
