.. _usage:

*****
Usage
*****

Here is the command-line help:

.. code-block:: bash

   $> time_axis -h
   usage: timeaxis.py -p PROJECT [-C CONFIG] [-h] (-c | -w | -f) [-l [LOGDIR]]
                      [-v] [-V]
                      [directory]

   Rewrite and/or check time axis into MIP NetCDF files, considering
   (i) uncorrupted filename period dates and
   (ii) properly-defined times units, time calendar and frequency NetCDF attributes.

   Returned status:
   000: Unmodified time axis,
   001: Corrected time axis because wrong timesteps.
   002: Corrected time axis because of changing time units,
   003: Ignored time axis because of inconsistency between last date of time axis and
   end date of filename period (e.g., wrong time axis length),
   004: Corrected time axis deleting time boundaries for instant time,
   005: Ignored averaged time axis without time boundaries.

   positional arguments:
     directory             Variable path to diagnose following the DRS
                           (e.g., /prodigfs/esg/CMIP5/merge/NCAR/CCSM4/amip/day/atmos/cfDay/r7i1p1/v20130507/tas/).
                           

   optional arguments:
     -p PROJECT, --project PROJECT
                           Required project name corresponding to a section of the configuration file.
                           
     -C CONFIG, --config CONFIG
                           Path of configuration INI file
                           (default is ~/anaconda/lib/python2.7/site-packages/timeaxis/config.ini).
                           
     -h, --help            Show this help message and exit.
                           
     -c, --check           Check time axis squareness (default is True).
                           
     -w, --write           Rewrite time axis depending on checking
                           (includes --check ; default is False).
                           THIS ACTION DEFINITELY MODIFY INPUT FILES!
                           
     -f, --force           Force time axis writing overpassing checking step
                           (default is False).
                           THIS ACTION DEFINITELY MODIFY INPUT FILES!
                           
     -l [LOGDIR], --logdir [LOGDIR]
                           Logfile directory (default is working directory).
                           If not, standard output is used.
                           
     -v, --verbose         Verbose mode.
                           
     -V, --version         Program version.

   Developped by Levavasseur, G. (CNRS/IPSL) and Laliberte, F. (ExArch)

Tutorials
---------

Just check a MIP variable:

.. code-block:: bash

   $>time_axis /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb -p cmip5 -c
   Time diagnostic started for /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb
   Version:                 v1
   Frequency:               mon
   Calendar:                noleap
   Time units:              days since 0160-01-01
   Files to process:        1
   ==> Filename:            ccb_Amon_bcc-csm1-1_1pctCO2_r1i1p1_016001-029912.nc
   -> Timesteps:            1680
   -> Instant time:         False
   -> Time axis status:     000
   -> Time boundaries:      True
   -> New checksum:         None
   Time diagnostic completed (1 files scanned)

Scan a directory with verbosity:

.. code-block:: bash

   $>time_axis /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb -p cmip5 -c -v
   Time diagnostic started for /prodigfs/esg/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb
   Version:                 v1
   Frequency:               mon
   Calendar:                noleap
   Time units:              days since 0160-01-01
   Files to process:        1
   ==> Filename:            ccb_Amon_bcc-csm1-1_1pctCO2_r1i1p1_016001-029912.nc
   -> Start:                0160-01-01 00:00:00
   -> End:                  0299-12-01 00:00:00
   -> Last:                 0299-12-01 00:00:00
   -> Timesteps:            1680
   -> Instant time:         False
   -> Time axis status:     000
   -> Time boundaries:      True
   -> New checksum:         None
   -> Time axis:
   15.5 | 45.0 | 74.5 | 105.0 | 135.5 | 166.0 | 196.5 | 227.5 | 258.0 | 288.5 | 319.0 | 349.5 | 380.5 |
   [...]
   50901.0 | 50931.5 | 50962.5 | 50993.0 | 51023.5 | 51054.0 | 51084.5
   -> Theoretical axis:
   15.5 | 45.0 | 74.5 | 105.0 | 135.5 | 166.0 | 196.5 | 227.5 | 258.0 | 288.5 | 319.0 | 349.5 | 380.5 |
   [...]
   50901.0 | 50931.5 | 50962.5 | 50993.0 | 51023.5 | 51054.0 | 51084.5
   Time diagnostic completed (1 files scanned)

.. note:: The ``-v/--verbose`` raises the tracebacks of thread-processes (default is the "silent" mode).

To specify the configuration file:

.. code-block:: bash

   $> esg_mapfiles /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb -p cmip5 -c /path/to/configfile/config.ini

To use a logfile (the logfile directory is optionnal):

.. code-block:: bash

   $>time_axis /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb -p cmip5 -c -l
   $> cat /path/to/logfile/timeaxis-YYYYMMDD-HHMMSS-PID.log
   YYYY/MM/DD HH:MM:SS AM INFO Time diagnostic started for /prodigfs/esg/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/ccb
   YYYY/MM/DD HH:MM:SS AM WARNING Version:                 v1
   YYYY/MM/DD HH:MM:SS AM WARNING Frequency:               mon
   YYYY/MM/DD HH:MM:SS AM WARNING Calendar:                noleap
   YYYY/MM/DD HH:MM:SS AM WARNING Time units:              days since 0160-01-01
   YYYY/MM/DD HH:MM:SS AM INFO Files to process:        1
   YYYY/MM/DD HH:MM:SS AM INFO ==> Filename:            ccb_Amon_bcc-csm1-1_1pctCO2_r1i1p1_016001-029912.nc
   YYYY/MM/DD HH:MM:SS AM INFO -> Timesteps:            1680
   YYYY/MM/DD HH:MM:SS AM INFO -> Instant time:         False
   YYYY/MM/DD HH:MM:SS AM INFO -> Time axis status:     000
   YYYY/MM/DD HH:MM:SS AM INFO -> Time boundaries:      True
   YYYY/MM/DD HH:MM:SS AM INFO -> New checksum:         None
   YYYY/MM/DD HH:MM:SS AM INFO Time diagnostic completed (1 files scanned)
   YYYY/MM/DD HH:MM:SS PM INFO ==> Search complete.

The write-mode displays the same information and only modify the input files if necessary. Nevertheless, you can force to overwrite time axis (the checksum is automatically computed again):

.. code-block:: bash

   $> time_axis /path/to/your/archive/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/test -p cmip5 -f
   Time diagnostic started for /prodigfs/esg/CMIP5/output1/BCC/bcc-csm1-1/1pctCO2/mon/atmos/Amon/r1i1p1/v1/test
   Version:                 v1
   Frequency:               mon
   Calendar:                noleap
   Time units:              days since 0160-01-01
   Files to process:        1
   ==> Filename:            ccb_Amon_bcc-csm1-1_1pctCO2_r1i1p1_016001-029912.nc
   -> Timesteps:            1680
   -> Instant time:         False
   -> Time axis status:     000
   -> Time boundaries:      True
   -> New checksum:         3c81206ad871acc38b9fa32d738669e9
   Time diagnostic completed (1 files scanned)
