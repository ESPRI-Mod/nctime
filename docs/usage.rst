.. _usage:


Generic usage
=============

.. note:: All the following arguments can be safely combined and add to the subcommand arguments.

Check the help
**************

.. code-block:: bash

    $> nctime {-h,--help}
    $> nctime SUBCOMMAND {-h,--help}

Check the version
*****************

.. code-block:: bash

    $> nctime {-v,--version}

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

The ``-p/--project`` argument is used to parse the corresponding configuration INI file. It is **always required**
(except for ``fetch-ini`` subcommand). This argument is case-sensitive and has to correspond to a section name of
the configuration file(s).

.. code-block:: bash

    $> nctime SUBCOMMAND {-p,--project} PROJECT_ID

.. note::
    If not submitted it takes the PROJECT_ID from the netCDF global attribute of the first file scanned.

Submit a configuration directory
********************************

By default, the configuration files are fetched or read from ``/esg/config/esgcet`` that is the usual configuration
directory on ESGF nodes. If you're preparing your data outside of an ESGF node, you can submit another directory to
fetch and read the configuration files.

.. code-block:: bash

    $> nctime SUBCOMMAND -i /PATH/TO/CONFIG/

.. note::
    If not submitted it takes the $ESGINI environment variable. If not exists the usual datanode path is used (i.e., ``/esg/config/esgcet``)

Use filters
***********

``nctime`` subcommands will scan your local archive to achieve data quality check. In such a scan, you can filter the file discovery by using a Python regular expression
(see `re <https://docs.python.org/2/library/re.html>`_ Python library).

The default is to walk through your local filesystem ignoring the hidden folders.
It can be change with:

.. code-block:: bash

    $> nctime SUBCOMMAND --ignore-dir PYTHON_REGEX

``nctime`` only considers unhidden NetCDF files by default excuding the regular expression ``^\..*$`` and
including the following one ``.*\.nc$``. It can be independently change with:

.. code-block:: bash

    $> nctime SUBCOMMAND --include-file PYTHON_REGEX --exclude-file PYTHON_REGEX

Keep in mind that ``--ignore-dir`` and ``--exclude-file`` specifie a directory pattern **NOT** to be matched, while
``--include-file`` specifies a filename pattern **TO BE** matched.

Use a logfile
*************

All errors and exceptions are logged into a file named ``nctime-YYYYMMDD-HHMMSS-PID.err``.
Other information are logged into a file named ``nctime-YYYYMMDD-HHMMSS-PID.log`` only if ``--log`` is submitted.
If not, the standard output is used following the verbose mode.
By default, the logfiles are stored in a ``logs`` folder created in your current working directory (if not exists).
It can be changed by adding a optional logfile directory to the flag.

.. code-block:: bash

    $> nctime SUBCOMMAND {-l,--log}
    $> nctime SUBCOMMAND -l /PATH/TO/LOGDIR/

Use multiprocessing
*******************

``nctime`` uses a multiprocessing interface. This is useful to process a large amount of data, especially in the case
of ``axis`` subcommands with the time axis calculation. Set the number of maximal processes to simultaneously treat
several files. One process seems sequential processing (the default). Set it -1 to use all available CPU processes
(as returned by ``multiprocessing.cpu_count()``). Default is set to 4 processes.

.. code-block:: bash

    $> nctime SUBCOMMAND --max-processes 4

.. warning:: The number of maximal processes is limited to the maximum CPU count in any case.

Exit status
***********

 * Status = 0
    All the files have been successfully processed without errors.
 * Status = 1
    Errors occur during file scanning and quality checkup.
 * Status = -1
    Argument parsing error.