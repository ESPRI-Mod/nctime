# time_axis.py

## Description

Time axis often is mistaken in CMIP5 files and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the time axis description.  We developed a Python program to check and rebuild a CMIP5-compliant time axis if necessary.

```time_axis.py``` is a Python command-line tool allowing you to easily check and/or rewrite time axis of your downloade files from ESG-F.

BECARFUL: this script is based on (i) uncorrupted filename period dates and (ii) properly-defined times units, time calendar and frequency NetCDF attributes.

## Features

- Always check time axis squareness depending on calendar, frequency, realm and time units,
- Check consistency between last theoretical date and end date in filename,
- Correct all mistaken timesteps,
- Delete time boundaries if necessary,
- Change time unites according to CMIP5 requirements if necessary,
- Diagnostic in output file or not,
- File multithreading,
- Save new checksum of modified files,
- Possibility to init a logger.

## Installing

To execute ```time_axis.py``` you has to be logged on filesystem hosting data.

Fork this GitHub project or download the Python script and its configuration file:

```Shell
wget http://dods.ipsl.jussieu.fr/glipsl/time_axis.py
```

## Configuring

No configuration is required.
The number of threads can be change on line 29 (default is 4 threads).

```Python
# Throttle upon number of threads to spawn
_THREAD_POOL_SIZE = 4
```

## Dependencies

```time_axis.py``` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:

- os, sys, re, logging
- argparse
- uuid
- numpy
- datetime
- multiprocessing
- textwrap

Please install the ```netCDF4``` python library not inclued in most Python distributions:

```Shell
pip install netCDF4
```

To support some corrections, NCO operators are required and can be installed as follows: [http://nco.sourceforge.net/#Binaries]

## Usage

```Shell
$> ./time_axis.py -h
usage: time_axis.py [-h] (-c | -w | -f) [-o [OUTDIAG]] [-l [LOGDIR]] [-v] [-V]
                    [directory]

Rewrite and/or check CMIP5 file time axis on CICLAD filesystem, considering
(i) uncorrupted filename period dates and
(ii) properly-defined times units, time calendar and frequency NetCDF attributes.

Returned status:
000: Unmodified time axis,
001: Corrected time axis because wrong timesteps.
002: Corrected time axis because of changing time units,
003: Ignored time axis because of inconsistency between last date of time axis and
end date of filename period (e.g., wrong time axis length),
004: Corrected time axis deleting time boundaries for instant time.

positional arguments:
  directory             Dataset path to browse following CMIP5 DRS
                        (e.g., /prodigfs/esg/CMIP5/merge/NCAR/CCSM4/amip/day/atmos/cfDay/r7i1p1/v20130507/tas/).


optional arguments:
  -h, --help            Show this help message and exit.

  -c, --check           Check time axis squareness (default is True).

  -w, --write           Rewrite time axis depending on checking
                        (includes --check ; default is False).
                        THIS ACTION DEFINITELY MODIFY INPUT FILES!

  -f, --force           Force time axis writing overpassing checking step
                        (default is False).
                        THIS ACTION DEFINITELY MODIFY INPUT FILES!

  -o [OUTDIAG], --outdiag [OUTDIAG]
                        Output diagnostic file (default is '{workdir}/time_axis.diag').

  -l [LOGDIR], --logdir [LOGDIR]
                        Logfile directory (default is working directory).
                        If not, standard output is used.

  -v, --verbose         Verbose mode.

  -V, --version         Program version.

Developped by Levavasseur, G. (CNRS/IPSL) and Laliberte, F. (ExArch)
```

## Examples

- Run the script with verbosity in check-mode:

```Shell
$> ./time_axis.py /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/co3satcalc/ -c -v
Diagnostic started for /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/co3satcalc
Version = v20120430
Frequency = yr
Calendar = noleap
Time units = days since 1850-01-01 00:00:00
Files to process = 2
==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1850-1949.nc
-> Start:                                                                        1850-01-01 00:00:00
-> End:                                                                          1949-01-01 00:00:00
-> Last:                                                                         1949-01-01 00:00:00
-> Timesteps:                                                                                    100
-> Instant time:                                                                               False
-> Time axis status:                                                                             000
-> Time boundaries:                                                                             True
-> New checksum:                                                                                None
-> Time axis:
182.5 | 547.5 | 912.5 | 1277.5 | 1642.5 | 2007.5 | 2372.5 | 2737.5 | 3102.5 | 3467.5 | 3832.5 |
4197.5 | 4562.5 | 4927.5 | 5292.5 | 5657.5 | 6022.5 | 6387.5 | 6752.5 | 7117.5 | 7482.5 | 7847.5 |
8212.5 | 8577.5 | 8942.5 | 9307.5 | 9672.5 | 10037.5 | 10402.5 | 10767.5 | 11132.5 | 11497.5 |
11862.5 | 12227.5 | 12592.5 | 12957.5 | 13322.5 | 13687.5 | 14052.5 | 14417.5 | 14782.5 | 15147.5 |
15512.5 | 15877.5 | 16242.5 | 16607.5 | 16972.5 | 17337.5 | 17702.5 | 18067.5 | 18432.5 | 18797.5 |
19162.5 | 19527.5 | 19892.5 | 20257.5 | 20622.5 | 20987.5 | 21352.5 | 21717.5 | 22082.5 | 22447.5 |
22812.5 | 23177.5 | 23542.5 | 23907.5 | 24272.5 | 24637.5 | 25002.5 | 25367.5 | 25732.5 | 26097.5 |
26462.5 | 26827.5 | 27192.5 | 27557.5 | 27922.5 | 28287.5 | 28652.5 | 29017.5 | 29382.5 | 29747.5 |
30112.5 | 30477.5 | 30842.5 | 31207.5 | 31572.5 | 31937.5 | 32302.5 | 32667.5 | 33032.5 | 33397.5 |
33762.5 | 34127.5 | 34492.5 | 34857.5 | 35222.5 | 35587.5 | 35952.5 | 36317.5
-> Theoretical axis:
182.5 | 547.5 | 912.5 | 1277.5 | 1642.5 | 2007.5 | 2372.5 | 2737.5 | 3102.5 | 3467.5 | 3832.5 |
4197.5 | 4562.5 | 4927.5 | 5292.5 | 5657.5 | 6022.5 | 6387.5 | 6752.5 | 7117.5 | 7482.5 | 7847.5 |
8212.5 | 8577.5 | 8942.5 | 9307.5 | 9672.5 | 10037.5 | 10402.5 | 10767.5 | 11132.5 | 11497.5 |
11862.5 | 12227.5 | 12592.5 | 12957.5 | 13322.5 | 13687.5 | 14052.5 | 14417.5 | 14782.5 | 15147.5 |
15512.5 | 15877.5 | 16242.5 | 16607.5 | 16972.5 | 17337.5 | 17702.5 | 18067.5 | 18432.5 | 18797.5 |
19162.5 | 19527.5 | 19892.5 | 20257.5 | 20622.5 | 20987.5 | 21352.5 | 21717.5 | 22082.5 | 22447.5 |
22812.5 | 23177.5 | 23542.5 | 23907.5 | 24272.5 | 24637.5 | 25002.5 | 25367.5 | 25732.5 | 26097.5 |
26462.5 | 26827.5 | 27192.5 | 27557.5 | 27922.5 | 28287.5 | 28652.5 | 29017.5 | 29382.5 | 29747.5 |
30112.5 | 30477.5 | 30842.5 | 31207.5 | 31572.5 | 31937.5 | 32302.5 | 32667.5 | 33032.5 | 33397.5 |
33762.5 | 34127.5 | 34492.5 | 34857.5 | 35222.5 | 35587.5 | 35952.5 | 36317.5
==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc
-> Start:                                                                        1950-01-01 00:00:00
-> End:                                                                          1989-01-01 00:00:00
-> Last:                                                                         1989-01-01 00:00:00
-> Timesteps:                                                                                     40
-> Instant time:                                                                               False
-> Time axis status:                                                                             000
-> Time boundaries:                                                                             True
-> New checksum:                                                                                None
-> Time axis:
36682.5 | 37047.5 | 37412.5 | 37777.5 | 38142.5 | 38507.5 | 38872.5 | 39237.5 | 39602.5 | 39967.5 |
40332.5 | 40697.5 | 41062.5 | 41427.5 | 41792.5 | 42157.5 | 42522.5 | 42887.5 | 43252.5 | 43617.5 |
43982.5 | 44347.5 | 44712.5 | 45077.5 | 45442.5 | 45807.5 | 46172.5 | 46537.5 | 46902.5 | 47267.5 |
47632.5 | 47997.5 | 48362.5 | 48727.5 | 49092.5 | 49457.5 | 49822.5 | 50187.5 | 50552.5 | 50917.5
-> Theoretical axis:
36682.5 | 37047.5 | 37412.5 | 37777.5 | 38142.5 | 38507.5 | 38872.5 | 39237.5 | 39602.5 | 39967.5 |
40332.5 | 40697.5 | 41062.5 | 41427.5 | 41792.5 | 42157.5 | 42522.5 | 42887.5 | 43252.5 | 43617.5 |
43982.5 | 44347.5 | 44712.5 | 45077.5 | 45442.5 | 45807.5 | 46172.5 | 46537.5 | 46902.5 | 47267.5 |
47632.5 | 47997.5 | 48362.5 | 48727.5 | 49092.5 | 49457.5 | 49822.5 | 50187.5 | 50552.5 | 50917.5
Diagnostic completed
```

- Run the script with a logfile and a diagnostic file:

```Shell
$> ./time_axis.py /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/co3satcalc/ -c -l -o

$> ls -l
-rw-r--r-- 1 glipsl 1.5K Mar 27 18:11 time_axis.diag
-rw-r--r-- 1 glipsl 2.0K Mar 27 18:11 time_axis-20150327-181131-20214.log
-rw-r--r-- 1 glipsl  14K Mar 27 18:11 README.md
-rwxr-xr-x 1 glipsl  36K Mar 27 18:10 time_axis.py*

$> cat time_axis.diag
Diagnostic started for /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/co3satcalc
Version = v20120430
Frequency = yr
Calendar = noleap
Time units = days since 1850-01-01 00:00:00
Files to process = 2
==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1850-1949.nc
-> Timesteps:                                                                                    100
-> Instant time:                                                                               False
-> Time axis status:                                                                             000
-> Time boundaries:                                                                             True
-> New checksum:                                                                                None
==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc
-> Timesteps:                                                                                     40
-> Instant time:                                                                               False
-> Time axis status:                                                                             000
-> Time boundaries:                                                                             True
-> New checksum:                                                                                None
Diagnostic completed

$> cat time_axis-20150327-181131-20214.log
2015/03/27 06:11:31 PM INFO Diagnostic started for /prodigfs/esg/CMIP5/output1/IPSL/IPSL-CM5A-LR/1pctCO2/yr/ocnBgchem/Oyr/r1i1p1/v20120430/co3satcalc
2015/03/27 06:11:31 PM WARNING Version = v20120430
2015/03/27 06:11:31 PM WARNING Frequency = yr
2015/03/27 06:11:31 PM WARNING Calendar = noleap
2015/03/27 06:11:31 PM WARNING Time units = days since 1850-01-01 00:00:00
2015/03/27 06:11:31 PM INFO Files to process = 2
2015/03/27 06:11:34 PM INFO ==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1850-1949.nc
2015/03/27 06:11:34 PM INFO -> Timesteps:                                                                                    100
2015/03/27 06:11:34 PM INFO -> Instant time:                                                                               False
2015/03/27 06:11:34 PM INFO -> Time axis status:                                                                             000
2015/03/27 06:11:34 PM INFO -> Time boundaries:                                                                             True
2015/03/27 06:11:34 PM INFO -> New checksum:                                                                                None
2015/03/27 06:11:34 PM INFO ==> Filename:                                co3satcalc_Oyr_IPSL-CM5A-LR_1pctCO2_r1i1p1_1950-1989.nc
2015/03/27 06:11:34 PM INFO -> Timesteps:                                                                                     40
2015/03/27 06:11:34 PM INFO -> Instant time:                                                                               False
2015/03/27 06:11:34 PM INFO -> Time axis status:                                                                             000
2015/03/27 06:11:34 PM INFO -> Time boundaries:                                                                             True
2015/03/27 06:11:34 PM INFO -> New checksum:                                                                                None
2015/03/27 06:11:34 PM INFO Diagnostic completed
```

- The write-mode only modify input files if necessary !

## Frequently asked questions

## Developpers/Authors

LEVAVASSEUR, G. (CNRS/IPSL)
LALIBERTE, F. (ExArch)

## Contacts

To submit bugs, suggestions or ideas: glipsl@ipsl.jussieu.fr or frederic.laliberte@utoronto.ca

## Changlog

2015-03-27 - Imporve logging and synda call. 

2015-03-24 - Includes synda post-processing call. 

2015-02-25 - Includes new corrections, logger and diagnostic output file. 
