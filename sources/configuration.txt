.. _configuration:

Configuration
=============

The only configuration you have to do at least is to define:
 * the maximal threads number (default is 4 threads),
 * the checksum type (default is SHA256).

Both under the ``[DEFAULT]`` section in the configuration INI file.

.. code-block:: ini

   [DEFAULT]
   max_threads = 3
   checksum_type = SHA256

The configuration file is included in the package and is in the default installation directory of your Python
packages. Feel free to copy it and made your own using the ``-i`` option (see :ref:`usage`).


Add a new project
*****************

Edit the ``config.ini`` as follows:

1. Define your "project" section in brackets:

.. code-block:: ini

   [your_project]

.. warning:: The ``--project`` option directly refers to the name of "project" sections.

2. Define the filename format of your project. The ``filename_format`` uses a regular expression to match the period
dates from the filename to process.

.. code-block:: ini

   filename_format = ([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\d]+)-([\d]+).nc

.. warning:: Feel free to defined a new filename format using the INI variable patterns.  The
    filename format must include two groups of digits called ``%(start_period)s`` and ``%(end_period)s``.

.. warning:: ``nctime`` only supports NetCDF files.

3. Declare all tuples of attributes requiring instantaneous time axis. For example, CMIP5 datasets using an
instantaneous time axis can be targeted using a tuple composed by the variable, the frequency and the realm of the DRS.

.. code-block:: ini

   need_instant_time = [(tuple1), (tuple2), ...]

4. Define the default time units if fixed by the *Data Reference Syntax* (DRS) of your project.

.. code-block:: ini

   time_units_default = days since 1949-12-01 00:00:00
