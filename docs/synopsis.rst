.. _synopsis:

********
Synopsis
********

NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely used following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and time are included in NetCDF files as vectors.

The time axis is a key dimension. Unfortunately, this time axis often is mistaken in files from coupled climate models and leads to flawed studies or unused data. Consequently, these files cannot be used or, even worse, produced erroneous results, due to problems in the time axis description.

``time_axis`` is a command-line tool allowing you to easily check and rebuild a MIP-compliant time axis of your downloaded files from the `ESG-F <http://pcmdi9.llnl.gov/>`_.

.. warning:: ``time_axis`` is based on uncorrupted filename period dates and properly-defined times units, time calendar and frequency NetCDF attributes.


Features
++++++++

**Time axis squareness**
   The theoretical time axis is always rebuilt depending on the calendar, the frequency, the realm and the time units. These information are extracted from the DRS tree of your file or the NetCDF attributes. Both time axis are rigorously compared to detect any mistakes.

.. note::
   
   ``time_axis`` checks:
    * all timesteps,
    * all time increments,
    * the consistency between the latest theoretical date and the end date from the filename,
    * the time units (following the CF and MIP requirements),
    * the time axis type (instantaneous or not),
    * the absence/presence of time boudaries.

**Multi-project**
   ``time_axis`` is currently provided supporting `CMIP5 <http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf>`_ and `CORDEX <https://www.medcordex.eu/cordex_archive_specifications_2.2_30sept2013.pdf>`_ *Data Reference Syntax* (DRS). Nevertheless, you can easily add a new "project" section in the configuration file to support yours. Please follow the `INI syntax <https://en.wikipedia.org/wiki/INI_file>`_.

**No duplicated files**
   A process file is open with both read and write access. This allows a faster file processing just reading the required metadata and the time axis. We choose to directly overwrite the time axis into the original file avoiding to duplicate the file. *Consequently, the write (*``-w/--write``* and *``-f/--force``*) mode definitely modify the original input files*.  The modifications are only apply on time axis and/or time attributes. ``time_axis`` never reads the other dimensions or the variable(s) described into the NetCDF.

**Ignore files with missing timesteps**
   When a time axis has a wrong length, the error is raised but not corrected because of inability to add/delete timesteps to a file currently.

**Delete time boundaries if necessary**
   An instantaneous time axis do not embed time boundaries. If an instantaneous time axis is detected with time boundaries, they are deleted using `NCO operators <http://nco.sourceforge.net/>`_. In this case only, the file is duplicated.

**CF-MIP time units requirements**
   Into a MIP atomic dataset (i.e., the variable level from the DRS tree) the NetCDF files are splitted depending on the model and the frequency over a time period. This requires the same time units for all files into the same atmic dataset (at least) and fixed by the first file of the period. Moreover, the times units has to be declared with the following format: ``days since YYYY-MM-DD HH:mm:ss``.

**Multithreading**
   To check the time axis of a lot of high frequency files becomes time consuming. We implement multithreading at file level. Each file is processed by a thread that runs the time axis diagnostic.

**Keep threads tracebacks**
  The threads-processes do not shutdown the main process of ``time_axis`` run. If an error occurs on a thread, the traceback of the child-process is not raised to the main process. To help you to have a fast debug, the tracebacks of each threads can be raised using the ``-v/--verbose`` option (see :ref:`usage`).

**Developer's entry point**
  ``time_axis`` can be imported and called in your own scripts. Just pass a dictionnary with your flags to the ``run(job={})`` function (see :ref:`autodoc`). 

**Use a logfile**
   You can initiate a logger instead of the standard output. This could be useful for automatic workflows. The logfile name is automatically defined and unique (using the the job's name, the date and the job's PID). You can define an output directory for your logs too.
