.. _usage:

Usage and tutorials
===================

Common usage
************

Specify the project
-------------------

.. code-block:: bash

    $> nctime <command> --project <project_id>

.. warning:: This ``--project`` argument is always required.

.. warning:: This ``--project`` name has to correspond to a section of the configuration file.

.. warning:: The ``--project`` is case-sensitive.


Specify a configuration file
----------------------------

.. code-block:: bash

   $> nctime <command> -i /path/to/config.ini

.. note:: Default is ``$PWD/config.ini``.


Add verbosity
-------------

.. code-block:: bash

   $> nctime <command> -v

Show help message and exit
--------------------------

.. code-block:: bash

   $> nctime <command> -h

Use a logfile
-------------

.. code-block:: bash

   $> nctime <command> --log /path/to/logdir
   [...]
   $> cat /path/to/logdir/nctime-YYYYMMDD-HHMMSS-PID.log
   [...]

.. note:: The logfile directory is optional.

.. note:: If not submitted the logfile directory is read from the configuration file first or is the current working
   directory instead. No flag seems the standard output is used.

``nctime overlap``
******************

Check a MIP variable
--------------------

.. code-block:: bash

   $> nctime overlap --project <project_id> /path/to/your/archive/project/variable/ -v
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO Create edges from source nodes to target nodes
   YYYY/MM/DD HH:MM:SS PM INFO -- START -- --> file1.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file2.nc  --> -- END --
   YYYY/MM/DD HH:MM:SS PM INFO Shortest path found
   YYYY/MM/DD HH:MM:SS PM INFO No overlapping files
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic completed

Detect overlapping files
------------------------

.. code-block:: bash

   $> nctime overlap --project <project_id> /path/to/your/archive/project/variable/ -v
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO Create edges from source nodes to target nodes
   YYYY/MM/DD HH:MM:SS PM INFO -- START -- --> file1.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file2.nc  --> file2.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file3.nc  --> -- END --
   YYYY/MM/DD HH:MM:SS PM INFO Shortest path found
   YYYY/MM/DD HH:MM:SS PM WARNING Overlapping files:
   YYYY/MM/DD HH:MM:SS PM WARNING file2.nc
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic completed

Remove overlapping files
------------------------

.. code-block:: bash

   $> nctime overlap --project <project_id> /path/to/your/archive/project/variable/ -v --resolve
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO Create edges from source nodes to target nodes
   YYYY/MM/DD HH:MM:SS PM INFO -- START -- --> file1.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file2.nc  --> file2.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file3.nc  --> -- END --
   YYYY/MM/DD HH:MM:SS PM INFO Shortest path found
   YYYY/MM/DD HH:MM:SS PM WARNING Overlapping files:
   YYYY/MM/DD HH:MM:SS PM WARNING file2.nc <- REMOVED
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic completed

Detect a time gap
-----------------

.. code-block:: bash

   $> nctime overlap --project <project_id> /path/to/your/archive/project/variable/ -v
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO Create edges from source nodes to target nodes
   YYYY/MM/DD HH:MM:SS PM INFO -- START -- --> file1.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file2.nc  --> file2.nc
   YYYY/MM/DD HH:MM:SS PM INFO   file3.nc  --> -- END --
   YYYY/MM/DD HH:MM:SS PM WARNING No shortest path found.
   YYYY/MM/DD HH:MM:SS PM INFO No overlapping files
   YYYY/MM/DD HH:MM:SS PM INFO Overlap diagnostic completed

.. warning:: To resolve only full overlaps please use the ``--full-overlap-only`` flag.

``nctime axis``
***************

Check a MIP variable
--------------------

.. code-block:: bash

   $> nctime axis --project <project_id> /path/to/your/archive/project/variable/ -v
   YYYY/MM/DD HH:MM:SS PM INFO Time axis diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO Time diagnostic completed (3 files scanned)

.. note:: Verbosity will print file information with theoretical time axis and time axis from file.

Detect a wrong time axis
------------------------

   $> nctime axis --project <project_id> /path/to/your/archive/project/variable/ -v
   YYYY/MM/DD HH:MM:SS PM INFO Time axis diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - 001 - Mistaken time axis over one or several time steps
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO Time diagnostic completed (3 files scanned)

Rewrite a wrong time axis
-------------------------

.. note:: The write mode displays the same information and only modify the input files if necessary. In such a case,
   the new checksum is computed automatically.

.. code-block:: bash

   $> nctime axis --project <project_id> /path/to/your/archive/project/variable/ -v --write
   YYYY/MM/DD HH:MM:SS PM INFO Time axis diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - 001 - Mistaken time axis over one or several time steps
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO Time diagnostic completed (3 files scanned)

Force a time axis rewriting
---------------------------

.. note:: Anyway, you can force to overwrite time axis (the checksum is automatically computed again).

.. code-block:: bash

   $> nctime axis --project <project_id> /path/to/your/archive/project/variable/ -v --force
   YYYY/MM/DD HH:MM:SS PM INFO Time axis diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - 001 - Mistaken time axis over one or several time steps
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO Time diagnostic completed (3 files scanned)

Save diagnostic to an SQL database
----------------------------------

.. code-block:: bash

   $> nctime axis --project <project_id> /path/to/your/archive/project/variable/ -v --db
   YYYY/MM/DD HH:MM:SS PM INFO Time axis diagnostic started for /path/to/your/archive/project/variable/
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file1.nc - Diagnostic persisted into database
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file2.nc - Diagnostic persisted into database
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Time axis seems OK
   YYYY/MM/DD HH:MM:SS PM INFO file3.nc - Diagnostic persisted into database
   YYYY/MM/DD HH:MM:SS PM INFO Time diagnostic completed (3 files scanned)

   $> sqlite3 time_axis.db
   $sqlite> .schema
   CREATE TABLE time_axis
               (id INTEGER PRIMARY KEY,
               project TEXT,
               realm TEXT,
               frequency TEXT,
               freq_units TEXT,
               variable TEXT,
               filename TEXT,
               start TEXT,
               end TEXT,
               last TEXT,
               length INT,
               file_units TEXT,
               status TEXT,
               file_ref TEXT,
               ref_units TEXT,
               calendar TEXT,
               is_instant INT,
               has_bounds INT,
               new_checksum TEXT,
               full_path TEXT,
               creation_date TEXT);

.. note:: The database path is optional.

.. note:: If not submitted the database path is read from the configuration file first or in the current working
   directory instead. No flag seems that the diagnostic is not recorded.