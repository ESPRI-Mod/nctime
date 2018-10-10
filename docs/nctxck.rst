.. _axis:

Check time axis squareness
==========================

Time is a key dimension from NetCDF files. Unfortunately, the time axis is often mistaken in files from coupled climate models and leads to flawed studies or
unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the
time axis description.

Rebuilt and check time axis
***************************

.. code-block:: bash

    $> nctxck /PATH/TO/SCAN/

Rewrite a wrong time axis
*************************

It displays the same information as above but also modify the input files ONLY IF NECESSARY (i.e., depending on the
check results):

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ {-w,--write}

.. warning:: We highly recommend to activate ``--write`` after a first dry-checking. This will definitely modify
    your input files. Be careful to activate ``--write`` when you are sure about time errors.

Force time axis rewriting
*************************

Anyway, you can force to overwrite time axis in any case:

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ {-f,--force}

Check an on going simulation
****************************

The "on-fly" mode allows to check an incomplete time axis which is by construct inconsistent with the end timestamp of the file name.
To disable the corresponding test and check the on going time axis squareness use:

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ --on-fly

Default is a deactivated "on-fly" mode.
``nctxck`` is able to deduce if your simulation is completed or not. In the last case, the "on-fly" mode is
automatically activated. You only need to submit the directory including both your ``config.card`` and ``run.card``
provided by the libIGCM framework:

.. code-block:: bash

    $> nctxck /PATH/TO/SCAN/ --card /PATH/TO/SUBMISSION/DIRECTORY

.. warning:: This option is only available if you run your simulation within the IPSL libICM framework.

Define starting and/or ending time stamps
*****************************************

Default is to consider for each file scanned the starting timestamp as true to rebuilt the theoretical time axis.
This allow to to process each file independently. Nevertheless, at least for debugging purpose, it could be useful
to submit another reference starting time stamp to make time axis rebuilding free from filename hypothesis:

.. code-block:: bash

    $> nctxck /PATH/TO/SCAN/ --start YYYYMMDD

.. note::
    The submitted time stamp will be completed to 14 digits. We highly recommend to submit a digit as most precise as possible for the first date of the time axis.

.. warning::
    Be careful this new submitted time stamp will be use to rebuilt time axis of all the file scanned.

The same can be done with the ending time stamp even if it is unused in time axis rebuilding:

.. code-block:: bash

    $> nctxck /PATH/TO/SCAN/ --end YYYYMMDD

.. note::
    Both flags can be used independently.

Show wrong time steps
*********************

By default ``nctxck`` print the first five wrong time steps if exist. This limit can be changed with:

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ --limit INTEGER

To print all wrong time steps:

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ --limit

.. note:: This limit is also used to print wrong time boundaries.

Ignore errors
*************

If some errors are known and expected in the diagnostic they can be ignore for a more lightweight output:

.. code-block:: bash

   $> nctxck /PATH/TO/SCAN/ --ignore-errors CODE,CODE


.. note::  The allowed error codes corresponds to the following axis status codes (e.g., 001, 002, etc.). One or
    several error coma-separated codes can be submitted.

Time axis status
****************

Time axis error codes:

 * 000: Time axis seems OK
 * 001: Incorrect time axis over one or several time steps
 * 002: Time units must be unchanged for the same dataset
 * 003: Last date is earlier than end date from filename
 * 004: An instantaneous time axis should not embed time boundaries
 * 005: An averaged time axis should embed time boundaries
 * 006: Incorrect time bounds over one or several time steps
 * 007: Calendar must be unchanged for the same dataset
 * 008: Last date is later than end date of filename