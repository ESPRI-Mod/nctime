.. _synopsis:

Synopsis
========

NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely used
following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and time are
included in NetCDF files as vectors.

Time is a key dimension from NetCDF files that could lead to flawed studies or unused data if misdeclared. ``nctime``
allows researchers to easily diagnose the time definition of their data to ensure a proper analysis.

``nctime axis``
***************

Unfortunately, the time axis is often mistaken in files from coupled climate models and leads to flawed studies or
unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the
time axis description.

.. warning:: To rebuild a proper time axis, the dates from filename are expected to set the first time boundary and not
    the middle of the time interval. This is always the case for the instantaneous axis or frequencies greater than the
    daily frequency. Consequently, the 3-6 hourly files with an averaged time axis requires a date time correction.

``nctime overlap``
******************

To produce smaller files, the NetCDF files are splitted over the time period. Consequently, the different MIP archives
designs include the period dates into the filename. The scheme of chunked files in MIP projects is not fixed and depends
on several parameters (the institute, the model, the frequency, etc.). These different schemes lead to unnecessary
overlapping files with a more complex folder reading and wasting disk space.

.. note:: ``nctime`` is based on uncorrupted filename period dates and properly-defined times units, time calendar and
    frequency NetCDF attributes.

Key features
************

Time axis squareness
    The theoretical time axis is always rebuilt depending on the calendar, the frequency, the realm and the time units.
    These information are extracted from the DRS tree of your file or the NetCDF attributes. Both time axis are
    rigorously compared to detect any mistakes.

.. note::

   ``nctime axis`` checks:
    * all timesteps,
    * all time increments,
    * the consistency between the latest theoretical date and the end date from the filename,
    * the time units (following the CF and MIP requirements),
    * the time axis type (instantaneous or not),
    * the absence/presence of time boundaries.

Multi-project
    ``nctime axis`` is currently provided supporting `CMIP5
    <http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf>`_ and `CORDEX
    <https://www.medcordex.eu/cordex_archive_specifications_2.2_30sept2013.pdf>`_ *Data Reference Syntax* (DRS).
    Nevertheless, you can easily add a new "project" section in the configuration file to support yours. Please follow
    the `INI syntax <https://en.wikipedia.org/wiki/INI_file>`_.

No duplicated files
    A process file is open with both read and write access. This allows a faster file processing just reading the
    required metadata and the time axis. We choose to directly overwrite the time axis into the original file
    avoiding to duplicate the file. *Consequently, the write (*``--write``* and *``--force``*) mode definitely modify
    the original input files*. The modifications are only apply on time axis and/or time attributes. ``nctime axis``
    never reads the other dimensions or the variable(s) described into the NetCDF.

Delete time boundaries if necessary
    An instantaneous time axis do not embed time boundaries. If an instantaneous time axis is detected with time
    boundaries, they are deleted using `NCO operators <http://nco.sourceforge.net/>`_. In this case only, the file is
    duplicated.

CF-MIP time units requirements
    Into a MIP atomic dataset (i.e., the variable level from the DRS tree) the NetCDF files are splitted depending on
    the model and the frequency over a time period. This requires the same time units for all files into the same
    atomic dataset (at least) and fixed by the first file of the period. Moreover, the times units has to be
    declared with the following format: ``days since YYYY-MM-DD HH:mm:ss``.

Multi-threading
    To check the time axis of a lot of high frequency files becomes time consuming. We implement multithreading at
    file level. Each file is processed by a thread that runs the time axis diagnostic.

Tracebacks
    The threads-processes do not shutdown the main process of ``nctime axis`` run. If an error occurs on a thread, the
    traceback of the child-process is not raised to the main process. To help you to have a fast debug, the tracebacks
    of each threads can be raised using the ``-v`` option (see :ref:`usage`).

Use a logfile
    You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The
    logfile name is automatically defined and unique (using the the job's name, the date and the job's PID). You can
    define an output directory for your logs too.

Network analysis
    Each filename from the variable directory covers a part of the time period. ``nctime overlap`` builds a directed
    graph, that is, graphs with directed edges. Each node on the graph is a file defined by its first date and the
    date next to the end.

Looking for the shortest path
    ``nctime overlap`` uses a directed graph to find the shortest "date path" between all nodes, covering the whole
    time period. All excluded files from this "date path" are overlapping files. In the case of a gap in the time
    period, ``nctime overlap`` adds the possibility to use the longest subtree from the start date instead (i.e., the
    most consecutive files).

Overlap deletion
    All detected overlaps can be automatically removed using the ``--remove`` argument (see :ref:`usage`).
