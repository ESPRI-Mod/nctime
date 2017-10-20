.. _index:


``nctime`` toolbox
==================

NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely used
following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and time are
included in NetCDF files as vectors.

Time is a key dimension from NetCDF files that could lead to flawed studies or unused data if misdeclared. ``nctime``
allows researchers to easily diagnose the time definition of their data to ensure a proper analysis.

.. note:: ``nctime`` is based on uncorrupted filename period dates and properly-defined times units, time calendar
    and frequency NetCDF attributes.|n|n

.. toctree::
   :maxdepth: 1

   installation
   configuration
   usage
   overlap
   axis
   faq
   credits
   log
   autodoc
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
