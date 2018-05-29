.. _axis:


Check time axis squareness
==========================

Time is a key dimension from NetCDF files. Unfortunately, the time axis is often mistaken in files from coupled climate models and leads to flawed studies or
unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the
time axis description.

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

It displays the same information as above but also modify the input files ONLY IF NECESSARY (i.e., depending on the
check results):

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --write

.. warning:: We highly recommend to activate ``--write`` after a first dry-checking. This will definitely modify
    your input files. Be careful to activate ``--write`` when you are sure about time errors.

Force time axis rewriting
*************************

Anyway, you can force to overwrite time axis:

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --force

Check an on going simulation
****************************

The "on-fly" mode allows to check an incomplete time axis which is by construct inconsistent with the end timestamp of the file name.
To disable the corresponding test and check the on goind time axis squareness use:

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --on-fly

Show wrong time steps
*********************

By default ``nctime axis`` print the first five wrong time steps if exist. This limit can be changed with:

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --limit INTEGER

To print all wrong time steps:

.. code-block:: bash

   $> nctime axis --project PROJECT_ID /PATH/TO/SCAN/ --limit

Time axis status
****************

Time axis error codes:

 * 000: Time axis seems OK
 * 001: Incorrect time axis over one or several time steps
 * 002: Time units must be unchanged for the same dataset
 * 003: Last timestamp differs from end timestamp of filename
 * 004: An instantaneous time axis should not embed time boundaries
 * 005: An averaged time axis should embed time boundaries
 * 006: Incorrect time bounds over one or several time steps
 * 007: Calendar must be unchanged for the same dataset
 * 008: Last date differs from end date of filename

Exit status
***********

 * Status = 0
    All the files have been successfully scanned and the time axis seems correct or have been corrected.
 * Status = 1
    Some time axis contains errors and should be corrected.
