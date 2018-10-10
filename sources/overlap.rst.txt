.. _overlap:


Check time series continuity
============================

To produce smaller files, the NetCDF files are splitted over the time period. Consequently, the different archives
designs include the period dates into the filename. This scheme of chunked files in projects is not fixed and depends
on several parameters (the institute, the model, the time frequency, etc.). These different schemes lead to unnecessary
overlapping files with a more complex folder reading and wasting disk space. In addition, errors in the data production
or publication workflows can lead to broken time series.

``nctcck`` is designed to easily highlight broken time series or chunked NetCDF files
producing overlaps in a time series. It is able to delete all chunked overlapping files in your variable
directories in order to save disk space.

Detects overlaps or time gaps
*****************************

.. code-block:: bash

    $> nctcck /PATH/TO/SCAN/

By default, ``nctcck`` consider a time serie as broken when time gaps exist between netCDF time period.
Following the CMIP Data Request, some data can be asked only for sub-periods in the time serie, thus time gaps are expected.
To check compare broken time series against CMIP DR ``nctcck`` is able to use DR2XML files patterns to deduce if
a time gap is expected or not. To activate this just submit the directory including both your ``config.card`` and ``run.card``
provided by the libIGCM framework:

.. code-block:: bash

    $> nctcck /PATH/TO/SCAN/ --card /PATH/TO/SUBMISSION/DIRECTORY

.. warning:: This option is only available if you run your simulation within the IPSL libICM framework.

Remove overlapping files
************************

.. code-block:: bash

   $> nctcck /PATH/TO/SCAN/ {-r,--resolve}

.. warning:: We highly recommend to activate ``--resolve`` after a first dry-checking. This will potentially
    remove and/or rename files. Be careful to activate ``--resolve`` when you are sure about errors.

Remove full overlapping files only
**********************************

.. code-block:: bash

   $> nctcck /PATH/TO/SCAN/ --resolve --full-only

Define starting and/or ending period time stamps
************************************************

Default is to consider the start (end) of the period, respectively, as the minimum (maximum) of the filename timestamps for each dataset.
This could hide some missing files at the start or the end of the time period to cover. You can specify the start and end dates of the period
to cover by using respectively `--start` and `--end` flags.

.. code-block:: bash

    $> nctxck /PATH/TO/SCAN/ --start YYYYMMDD --end YYYYMMDD

.. note::
    The submitted time stamp will be completed to 14 digits. We highly recommend to submit a digit as most precise as possible for the first date of the time axis.

.. warning::
    Be careful this new submitted time stamp will be use to rebuilt time axis of all the file scanned.

.. note::
    Both flags can be used independently.