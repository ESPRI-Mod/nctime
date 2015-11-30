.. _configuration:

Configuration
=============

The only conguration you have to do at least is to define the threads number under the ``[DEFAULT]`` section in the configuration INI file. Edit the ``config.ini`` to set the number of threads you want (default is 4 threads).

.. code-block:: ini

   [DEFAULT]
   threads_number = 4

The configuration file is included in the package and is in the default installation directory of your Python packages (see ``time_axis -h``). Feel free to copy it and made your own using the ``-i`` option (see :ref:`usage`).

You can also define the checksum type you want in this section. MD5 (default) or SHA256 checksums are supported.

.. code-block:: ini

   checksum_type = SHA256


Add a new project
*****************

Edit the ``config.ini`` as follows:

1. Define your "project" section in brackets:

.. code-block:: ini

   [your_project]

.. warning:: The ``--project`` option directly refers to the name of "project" sections.

2. Define the *Data Reference Syntax* (DRS) tree of your project on your filesystem. The ``directory_format`` is requiered for auto-detection and uses a regular expression to match the DRS facets of the directory to scan.

.. code-block:: ini

   directory_format = /(?P<root>[\w./-]+)/(?P<project>[\w.-]+)/(?P<facet1>[\w.-]+)/(?P<facet2>[\w.-]+)/(?P<facet3>[\w.-]+)

.. warning:: Feel free to create/modify a tree if necessary using all regex facilities. Nevertheless, your DRS has to include at least the following facets "project", "frequency", "realm" (CMIP5 specific), "variable", "version".

3. Define the filename format of your project. The ``filename_format`` uses a regular expression to match the period dates in filename to process.

.. code-block:: ini

   filename_format = ([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\w.-]+)_([\d]+)-([\d]+).nc

.. warning:: Feel free to defined a new filename format using all regex facilities.  The filename format must end with two groups of digits. Becareful to keep the ``.nc`` extension because ``time_axis`` only supports NetCDF files.

4. Declare all tuples of attributes requiering instantaneous time axis. For example, CMIP5 datasets using an instantaneous time axis can be targeted using a tuple compsed by the variable, the frequency and the realm of the DRS.

.. code-block:: ini

   need_instant_time = [(tuple1), (tuple2), ...]

5. Define the default time units if fixed by the DRS of your project.

.. code-block:: ini

    time_units_default = days since 1949-12-01 00:00:00
