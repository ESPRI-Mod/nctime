.. _usage:


Generic usage
=============

.. note:: All the following arguments can be safely combined and add to the subcommand arguments.

Check the help
**************

.. code-block:: bash

    $> nctime -h
    $> nctime SUBCOMMAND -h

Check the version
*****************

.. code-block:: bash

    $> nctime -v

Debug mode
**********

.. code-block:: bash

    $> nctime SUBCOMMAND --debug

Print all results
*****************

Default is to only print errors, to change this and print all results:

.. code-block:: bash

    $> nctime SUBCOMMAND --all

Specify the project
*******************

The ``--project`` argument is used to parse the corresponding configuration INI file. It is **always required**
(except for ``fetch-ini`` subcommand). This argument is case-sensitive and has to correspond to a section name of
the configuration file(s).

.. code-block:: bash

    $> nctime SUBCOMMAND --project PROJECT_ID

Submit a configuration directory
********************************

By default, the configuration files are fetched or read from ``/esg/config/esgcet`` that is the usual configuration
directory on ESGF nodes. If you're preparing your data outside of an ESGF node, you can submit another directory to
fetch and read the configuration files.

.. code-block:: bash

    $> nctime SUBCOMMAND -i /PATH/TO/CONFIG/

.. note::
    If not submitted it takes the $ESGINI environment variable. If not exists the usual datanode path is used (i.e., ``/esg/config/esgcet``)

Use real filename dates
***********************

``nctime`` use the dates from the filename to start its processes. Due to different use cases, filename dates related
to 3-hourly and 6-hourly data are corrected by default to respectively start at 000000 end at 2100000 (180000) whether
the time axis is instantaneous or not. To disable this correction and stricly consider dates from filename to check the
time axis:

.. code-block:: bash

    $> nctime SUBCOMMAND --true-dates

Use a logfile
*************

All errors and exceptions are logged into a file named ``nctime-YYYYMMDD-HHMMSS-PID.err``.
Other information are logged into a file named ``nctime-YYYYMMDD-HHMMSS-PID.log`` only if ``--log`` is submitted.
If not, the standard output is used following the verbose mode.
By default, the logfiles are stored in a ``logs`` folder created in your current working directory (if not exists).
It can be changed by adding a optional logfile directory to the flag.

.. code-block:: bash

    $> nctime SUBCOMMAND --log
    $> nctime SUBCOMMAND --log /PATH/TO/LOGDIR/

Use multiprocessing
*******************

``nctime`` uses a multiprocessing interface. This is useful to process a large amount of data, especially in the case
of ``axis`` subcommands with the time axis calculation. Set the number of maximal processes to simultaneously treat
several files. One process seems sequential processing (the default). Set it -1 to use all available CPU processes
(as returned by ``multiprocessing.cpu_count()``). Default is set to 4 processes.

.. code-block:: bash

    $> nctime SUBCOMMAND --max-processes 4

.. warning:: The number of maximal processes is limited to the maximum CPU count in any case.
