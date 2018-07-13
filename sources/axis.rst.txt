.. _axis:


Check time axis squareness
==========================

Time is a key dimension from NetCDF files. Unfortunately, the time axis is often mistaken in files from coupled climate models and leads to flawed studies or
unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the
time axis description.

Rebuilt and check time axis
***************************

.. code-block:: bash

    $> nctime axis /PATH/TO/SCAN/

Rewrite a wrong time axis
*************************

It displays the same information as above but also modify the input files ONLY IF NECESSARY (i.e., depending on the
check results):

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ {-w,--write}

.. warning:: We highly recommend to activate ``--write`` after a first dry-checking. This will definitely modify
    your input files. Be careful to activate ``--write`` when you are sure about time errors.

Force time axis rewriting
*************************

Anyway, you can force to overwrite time axis in any case:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ {-f,--force}

Check an on going simulation
****************************

The "on-fly" mode allows to check an incomplete time axis which is by construct inconsistent with the end timestamp of the file name.
To disable the corresponding test and check the on going time axis squareness use:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --on-fly

Default is a deactivated "on-fly" mode.
``nctime axis`` is able to deduce if your simulation is completed or not. In the last case, the "on-fly" mode is
automatically activated. You only need to submit the directory including both your ``config.card`` and ``run.card``
provided by the libIGCM framework:

.. code-block:: bash

    $> nctime axis /PATH/TO/SCAN/ --card /PATH/TO/SUBMISSION/DIRECTORY

.. warning:: This option is only available if you run your simulation within the IPSL libICM framework.

Define starting and/or ending time stamps
*****************************************

Default is to consider for each file scanned the starting timestamp as true to rebuilt the theoretical time axis.
This allow to to process each file independently. Nevertheless, at least for debugging purpose, it could be useful
to submit another reference starting time stamp to make time axis rebuilding free from filename hypothesis:

.. code-block:: bash

    $> nctime axis /PATH/TO/SCAN/ --start YYYYMMDD

.. note::
    The submitted time stamp will be completed to 14 digits. We highly recommend to submit a digit as most precise as possible for the first date of the time axis.

.. warning::
    Be careful this new submitted time stamp will be use to rebuilt time axis of all the file scanned.

The same can be done with the ending time stamp even if it is unused in time axis rebuilding:

.. code-block:: bash

    $> nctime axis /PATH/TO/SCAN/ --end YYYYMMDD

Define ending time stamp
************************


Show wrong time steps
*********************

By default ``nctime axis`` print the first five wrong time steps if exist. This limit can be changed with:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --limit INTEGER

To print all wrong time steps:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --limit

.. note:: This limit is also used to print wring time boundaries.

Apply time correction on sud-daily frequencies
**********************************************

By default ``nctime`` use the dates from the filename to start its processes. Due to different use cases, filename dates related
to sub-daily data could not follow MIPs specifications. You can apply a time correction to respectively start sub-daily axis
at 000000 timestamp and end at 18000, 2100000, 230000, 233000 (depending on the frequency 6hr, 3hr, 1hr, subhr) whether
the time axis is instantaneous or not.

.. code-block:: bash

    $> nctime axis --correct-timestamp

Ignore errors
*************

If some errors are known and expected in the diagnostic they can be ignore for a more lightweight output:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --ignore-errors CODE,CODE


.. note::  The allowed error codes corresponds to the following axis status codes (e.g., 001, 002, etc.). One or
    several error coma-separated codes can be submitted.

Time axis status
****************

Time axis error codes:

 * 000: Time axis seems OK
 * 001: Incorrect time axis over one or several time steps
 * 002: Time units must be unchanged for the same dataset
 * 003a: Last timestamp is lower than end timestamp from filename
 * 003b: Last timestamp is higher than end timestamp from filename
 * 004: An instantaneous time axis should not embed time boundaries
 * 005: An averaged time axis should embed time boundaries
 * 006: Incorrect time bounds over one or several time steps
 * 007: Calendar must be unchanged for the same dataset
 * 008a: Last date is earlier than end date from filename
 * 008b: Last date is later than end date of filename