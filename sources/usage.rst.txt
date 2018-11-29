.. _usage:


Generic usage
=============

All the following arguments can be safely combined and add to each of the nctime **COMMAND**:
 - ``nctcck``
 - ``nctxck``


Check the help
**************

.. code-block:: bash

    $> COMMAND [SUBCOMMAND] {-h,--help}

Check the version
*****************

.. code-block:: bash

    $> COMMAND {-v,--version}

.. note:: The program version will be the same for all the nctime tools.

Debug mode
**********

Some progress bars informs you about the processing status of the different subcommands. You can switch to a more
verbose mode displaying each step with useful additional information.

.. code-block:: bash

    $> COMMAND {-d,--debug}

.. warning::
    This debug/verbose mode is silently activated in the case of a logfile (i.e., no progress bars).

Print all results
*****************

Default is to only print errors, to change this and print all results:

.. code-block:: bash

    $> COMMAND {-a,--all}

Specify the project
*******************

The ``-p/--project`` argument is used to parse the corresponding configuration INI file. This argument is case-sensitive and has to correspond to a section name of
the configuration file(s).

.. code-block:: bash

    $> nctime SUBCOMMAND {-p,--project} PROJECT_ID

.. note::
    If not submitted it takes the PROJECT_ID from the netCDF global attribute of the first file scanned.

Submit a configuration directory
********************************

By default, the configuration files are fetched or read from the ``$ESGINI_DIR`` environment variable. If not exists,
``/esg/config/esgcet`` that is the usual configuration directory on ESGF nodes is used. If you're checking your data outside of an ESGF node, you have to fetch those project-specific
INI files from `GitHub <https://github.com/ESGF/config/tree/master/publisher-configs/ini>`_ using the
`esgfetchini <http://esgf.github.io/esgf-prepare/fetchini.html>`_ command line from the
`esgprep library <http://esgf.github.io/esgf-prepare>`_. Then you can submit another directory to read the configuration files.

.. code-block:: bash

    $> COMMAND -i /PATH/TO/CONFIG/

Use a logfile
*************

Outputs can be logged into a file named ``PROG-YYYYMMDD-HHMMSS-PID.log``. If not, the standard output is used following the verbose mode.
By default, the logfiles are stored in a ``logs`` folder created in your current working directory (if not exists).
It can be changed by adding a optional logfile directory to the flag.

.. code-block:: bash

    $> COMMAND {-l,--log} [/PATH/TO/LOGDIR/]

Use filters
***********

``nctime`` tools will scan your local archive to achieve data quality check. In such a scan, you can filter the file discovery by using a Python regular expression
(see `re <https://docs.python.org/2/library/re.html>`_ Python library).

The default is to walk through your local filesystem ignoring the hidden folders. It can be change with:

.. code-block:: bash

    $> COMMAND --ignore-dir PYTHON_REGEX

``nctime`` only considers unhidden NetCDF files by default excuding the regular expression ``^\..*$`` and
including the following one ``.*\.nc$``. It can be independently change with:

.. code-block:: bash

    $> COMMAND --include-file PYTHON_REGEX --exclude-file PYTHON_REGEX

Keep in mind that ``--ignore-dir`` and ``--exclude-file`` specify a directory pattern **NOT** to be matched, while
``--include-file`` specifies a filename pattern **TO BE** matched.

Use multiprocessing
*******************

``nctime`` uses a multiprocessing interface. This is useful to process a large amount of data, especially in the case
of ``nctxck`` with the time axis calculation. Set the number of maximal processes to simultaneously treat
several files. One process seems sequential processing. Set it -1 to use all available CPU processes
(as returned by ``multiprocessing.cpu_count()``). Default is set to 4 processes.

.. code-block:: bash

    $> COMMAND --max-processes INTEGER

.. warning:: The number of maximal processes is limited to the maximum CPU count in any case.

Use libIGCM infos
*****************

.. warning:: This option is only available if you run your simulation within the IPSL libICM framework.

``nctime`` can use your libIGCM info to automatically apply some configuration. This requires to submit the
directory including both your ``config.card`` and ``run.card`` provided by the libIGCM framework:

.. code-block:: bash

    $> nctime SUBCOMMAND --card /PATH/TO/SUBMISSION/DIRECTORY

.. note:: This detailed documentation of ``nctcck`` and ``nctxck``.

Define a reference calendar
***************************

The reference calendar is the calendar use by ``nctime`` to rebuilt theoretical dates during the whole check.
By default, the reference calendar is one from the **FIRST** file scanned.
You can specify your own reference calendar with:

.. code-block:: bash

    $> COMMAND --calendar CALENDAR

.. note::
    Available calendars are those from CF conventions: gregorian, standard, proleptic_gregorian, noleap, 365_day, all_leap, 366_day, 360_day.

.. warning::
    The reference calendar is use for all the files scanned during the check.

Define reference time units
***************************

The reference time units are use by ``nctime`` to rebuilt theoretical dates during the whole check.
By default, the reference time units are those from the **FIRST** file scanned.
You can specify your own reference time units with:

.. code-block:: bash

    $> COMMAND --units "{seconds,minutes,hours,days} since YYYY-MM-DD [HH:mm:ss]"

.. note::
    Available units format is the one from CF conventions: "<units> since YYYY-MM-DD [HH:mm:ss]" where ``<units>`` stands for seconds, minutes, hours or days.

.. warning::
    The reference time units are use for all the files scanned during the check.

Overwrites a frequency increment
********************************

By default, each supported frequency as its own unit and increment (e.g. mon = 1 months). In some case the frequency
increment or units can be change, at least for diagnostic purposes. For finer modification, the increment is change for
a couple of MIP TABLE and FREQUENCY. The "all" keyword can be used to change the time increment for "all" table or "all"
frequencies values.

.. code-block:: bash

    $> COMMAND --set-inc TABLE:FREQUENCY=INCREMENT[+]UNITS

To change the time increment of sub-hourly files from the CFsubhr table from 30min to 15min:

.. code-block:: bash

    $> COMMAND --set-inc CFsubhr:subhrPt=15m

To change the time increment of all sub-hourly files whatever the MIP table:

.. code-block:: bash

    $> COMMAND --set-inc all:subhr=15m

To change the time increment of all CFsubhr files whatever the frequency:

.. code-block:: bash

    $> COMMAND --set-inc CFsubhr:all=15m

.. note::
    Duplicate the flag to overwrite several frequency increment.

.. note::
    Available increment units are: s (seconds), m (minutes), h (hours), D (days), M (months) and Y (years).

.. warning::
    Default increments are those expected by CMIP specifications. Overwrite them could lead to non CMIP-compliant files.

Exit status
***********

 * Status = 0
    All the files have been successfully processed without errors.
 * Status = N
    Errors occur during file scanning and quality checkup. N is the number of errors
 * Status = -1
    Argument parsing error.