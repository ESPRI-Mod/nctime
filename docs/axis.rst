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
To disable the corresponding test and check the on goind time axis squareness use:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --on-fly

Show wrong time steps
*********************

By default ``nctime axis`` print the first five wrong time steps if exist. This limit can be changed with:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --limit INTEGER

To print all wrong time steps:

.. code-block:: bash

   $> nctime axis /PATH/TO/SCAN/ --limit

.. note:: This limit is also used to print wring time boundaries.

Overwrites a frequency increment
********************************

By default, each supported frequency as its own unit and increment (e.g. mon = 1 months). In some case the frequency
increment can be change, at least for diagnostic purposes.

.. code-block:: bash

    $> nctime axis --set-inc FREQUENCY=INCREMENT

.. note::
    Duplicate the flag to overwrite several frequency increment.

.. warning::
    Default increments are those expected by CMIP specifications. Overwrite them could lead to non CMIP-compliant files.

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
 * 003: Last timestamp differs from end timestamp of filename
 * 004: An instantaneous time axis should not embed time boundaries
 * 005: An averaged time axis should embed time boundaries
 * 006: Incorrect time bounds over one or several time steps
 * 007: Calendar must be unchanged for the same dataset
 * 008: Last date differs from end date of filename
