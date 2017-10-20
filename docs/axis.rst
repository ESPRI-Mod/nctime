.. _axis:


Check time axis squareness
==========================

Time is a key dimension from NetCDF files. Unfortunately, the time axis is often mistaken in files from coupled climate models and leads to flawed studies or
unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the
time axis description.



    Time axis status returned:|n
    000: Unmodified time axis,|n
    001: Corrected time axis because wrong time steps,|n
    002: Corrected time axis because of changing time units,|n
    003: Corrected time axis because of inconsistency between last date of time axis and end date of filename
    period (e.g., wrong time axis length),|n
    004: Corrected time axis deleting time boundaries for instant time,|n
    005: Ignored averaged time axis without time boundaries,|n
    006: Corrected time bounds because wrong time steps.|n|n

Rebuilt and check time axis
***************************

.. code-block:: bash

    $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/

.. note:: To rebuild a proper time axis, the dates from filename are expected to set the first time boundary and
    not the middle of the time interval. This is always the case for the instantaneous axis or frequencies
    greater than the daily frequency. Consequently, the 3-6 hourly files with an averaged time axis requires a
    date time correction.

Rewrite a wrong time axis
*************************

It displays the same information as above but also modify the input files if necessary. In such a case, the
new checksum is computed automatically.

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --write

.. warning:: We highly recommend to activate ``--write`` after a first dry-checking. This will definitely modify
    your input files. Be careful to activate ``--write`` when you are sure about time errors.

Force time axis rewriting
*************************

Anyway, you can force to overwrite time axis (the checksum is automatically computed again).

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --force

Save diagnostic into an SQL database
************************************

When checking a large amount of file, it could be useful to serialize and record the checking results.
``nctime axis`` can store the time axis status properties into an SQLite database.

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --db
   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --db DB_FILE
   $> sqlite3 ./timeaxis.db
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

.. note:: The database path is optional. Default is ``CWD/timeaxis.db``.

Time axis status
****************

Time axis error codes:

 * 000: Time axis seems OK
 * 001: Mistaken time axis over one or several time steps
 * 002: Time units must be unchanged for the same dataset
 * 003: Last timestamp differs from end timestamp of filename
 * 004: An instantaneous time axis should not embed time boundaries
 * 005: An averaged time axis should embed time boundaries
 * 006: Mistaken time bounds over one or several time steps
 * 007: Calendar must be unchanged for the same dataset
 * 008: Last date differs from end date of filename

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and the time axis seems correct or have been corrected.
 * Status = 1
    Some time axis contains remains and should be manually corrected.
