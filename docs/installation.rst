.. _installation:

Installation
============

Usual PIP installation
**********************

.. code-block:: bash

  pip install timeaxis

PIP installation from GitHub
****************************

.. code-block:: bash

  pip install -e git://github.com/Prodiguer/cmip5-time-axis.git@master#egg=timeaxis

Installation from GitHub
************************

1. Create a new directory:

.. code-block:: bash

  mkdir timeaxis
  cd timeaxis

2. Clone `our GitHub project <https://github.com/Prodiguer/cmip5-time-axis>`_:

.. code-block:: bash

  git init
  git clone git@github.com:Prodiguer/cmip5-time-axis.git

3. Run the ``setup.py``:

.. code-block:: bash

  python setup.py install

4. The ``time_axis`` command-line is ready.


Dependencies
************

``time_axis`` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment includes:

 * `os <https://docs.python.org/2/library/os.html>`_, `glob <https://docs.python.org/2/library/glob.html>`_, `logging <https://docs.python.org/2/library/logging.html>`_, `re <https://docs.python.org/2/library/re.html>`_
 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `ConfigParser <https://docs.python.org/2/library/configparser.html>`_
 * `uuid <https://docs.python.org/2/library/uuid.html>`_
 * `functools <https://docs.python.org/2/library/functools.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_
 * `textwrap <https://docs.python.org/2/library/textwrap.html>`_

Please install the ``numpy`` and ``netCDF4`` libraries not inclued in most Python distributions using the usual PIP command-line:

.. code-block:: bash

   pip install numpy
   pip install netCDF

or download and intall the sources from PyPi for numpy<https://pypi.python.org/pypi/numpy>`_ and `netCDF <https://pypi.python.org/pypi/netCDF4>`_:

.. code-block:: bash

   wget https://pypi.python.org/packages/source/n/numpy/numpy-1.9.2.tar.gz#md5=a1ed53432dbcd256398898d35bc8e645
   cd numpy-1.9.2/
   python setup.py install
   wget https://pypi.python.org/packages/source/n/netCDF4/netCDF4-1.2.1.tar.gz#md5=9d9a7015ee98ec6766adc811d95b82c3
   cd netCDF4-1.2.1/
   python setup.py install

.. warning:: To support some corrections, `NCO operators <http://nco.sourceforge.net/#Binaries>`_ are required.

