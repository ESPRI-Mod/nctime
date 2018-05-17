.. _installation:


Installation
============

Usual PIP installation
**********************

.. code-block:: bash

   pip install nctime

PIP installation from GitHub
****************************

.. code-block:: bash

   pip install -e git://github.com/Prodiguer/nctime.git@master#egg=nctime

Installation from GitHub
************************

1. Clone `our GitHub project <https://github.com/Prodiguer/nctime>`_:

.. code-block:: bash

  git init
  git clone git@github.com:Prodiguer/nctime.git

3. Run the ``setup.py``:

.. code-block:: bash

  cd nctime
  python setup.py install

4. The ``nctime`` command-line is ready.


Dependencies
************

Linux distribution with Python 2.6+ is required. ``nctime`` uses the following basic Python libraries. Ensure that
your Python environment includes:

``nctime`` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment
includes:

 * `os <https://docs.python.org/2/library/os.html>`_
 * `re <https://docs.python.org/2/library/re.html>`_
 * `sys <https://docs.python.org/2/library/sys.html>`_
 * `logging <https://docs.python.org/2/library/logging.html>`_
 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `importlib <https://docs.python.org/2/library/importlib.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `textwrap <https://docs.python.org/2/library/textwrap.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_
 * `uuid <https://docs.python.org/2/library/uuid.html>`_

Some required libraries are not included in most Python distributions. Please install them using the usual PIP command:

 * `netCDF4 <http://unidata.github.io/netcdf4-python/>`_
 * `netcdftime <https://github.com/Unidata/netcdftime>`_
 * `nco <https://pypi.python.org/pypi/nco>`_
 * `numpy <http://www.numpy.org/>`_
 * `networkx <https://networkx.github.io/>`_
 * `ESGConfigParser <https://pypi.python.org/pypi/ESGConfigParser>`_
 * `fuzzywuzzy <https://pypi.python.org/pypi/fuzzywuzzy>`_

.. warning:: To support some corrections, `NCO operators <http://nco.sourceforge.net/#Binaries>`_ must be installed.