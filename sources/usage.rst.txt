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

Only print errors
*****************

.. code-block:: bash

    $> nctime SUBCOMMAND --errors-only

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
    In the case of ``fetch-ini`` subcommand, if you're not on an ESGF node and ``/esg/config/esgcet`` doesn't exist,
    the configuration file(s) are fetched into an ``ini`` folder in your working directory.

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
of ``axis`` subcommands with file checksum computation. Set the number of maximal threads to simultaneously process
several files (4 threads is the default and one seems sequential processing).

.. code-block:: bash

    $> nctime SUBCOMMAND --max-threads 4
