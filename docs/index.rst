.. _index:


.. code-block:: text

    ███╗   ██╗ ██████╗████████╗██╗███╗   ███╗███████╗
    ████╗  ██║██╔════╝╚══██╔══╝██║████╗ ████║██╔════╝
    ██╔██╗ ██║██║        ██║   ██║██╔████╔██║█████╗
    ██║╚██╗██║██║        ██║   ██║██║╚██╔╝██║██╔══╝
    ██║ ╚████║╚██████╗   ██║   ██║██║ ╚═╝ ██║███████╗
    ╚═╝  ╚═══╝ ╚═════╝   ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝

NetCDF files describe all dimensions necessary to work with. In the climate community, this format is widely used
following the `CF conventions <http://cfconventions.org/>`_. Dimensions such as longitude, latitude and time are
included in NetCDF files as vectors.

Time is a key dimension from NetCDF files that could lead to flawed studies or unused data if misdeclared. ``nctime``
allows researchers to easily diagnose the time definition of their data to ensure a proper analysis.

See the :ref:`faq` to learn more about what is behind the scene of ``nctime``.

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
