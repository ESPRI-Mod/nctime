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

``nctime`` uses the following basic Python libraries includes in Python 2.5+. Becareful your Python environment
includes:

 * `os <https://docs.python.org/2/library/os.html>`_
 * `re <https://docs.python.org/2/library/re.html>`_
 * `sys <https://docs.python.org/2/library/sys.html>`_
 * `logging <https://docs.python.org/2/library/logging.html>`_
 * `argparse <https://docs.python.org/2/library/argparse.html>`_
 * `ConfigParser <https://docs.python.org/2/library/configparser.html>`_
 * `datetime <https://docs.python.org/2/library/datetime.html>`_
 * `textwrap <https://docs.python.org/2/library/textwrap.html>`_
 * `functools <https://docs.python.org/2/library/functools.html>`_
 * `multiprocessing <https://docs.python.org/2/library/multiprocessing.html>`_
 * `uuid <https://docs.python.org/2/library/uuid.html>`_
 * `sqlite3 <https://docs.python.org/2.6/library/sqlite3.html>`_

Please install the ``numpy``, ``netCDF4``, ``nco`` and ``networkx`` libraries not included in most Python distributions
using the usual PIP command-line:

.. code-block:: bash

   pip install numpy
   pip install netCDF
   pip install nco
   pip install networkx

or download and install the sources from PyPi:

.. code-block:: bash

    wget https://pypi.python.org/packages/source/n/numpy/numpy-1.9.2.tar.gz#md5=a1ed53432dbcd256398898d35bc8e645
    cd numpy-1.9.2/
    python setup.py install

    wget https://pypi.python.org/packages/source/n/netCDF4/netCDF4-1.2.1.tar.gz#md5=9d9a7015ee98ec6766adc811d95b82c3
    cd netCDF4-1.2.1/
    python setup.py install

    wget https://pypi.python.org/packages/ae/9e/cea585e1964f8282881577033cd94ba30b89c0a883f1a59ede1d332bd4da/networkx-1.9.tar.gz#md5=683ca697a9ad782cb78b247cbb5b51d6
    cd networkx-1.9/
    python setup.py install

    wget https://pypi.python.org/packages/55/26/5b2d3b0edafafd85d1d1eeef341812fde6a1337ce473c430fcac90dc638d/nco-0.0.2.tar.gz#md5=bf7f543f7ffb5739eaf6466ca7e60c38
    cd nco-0.0.2/
    python setup.py install

.. warning:: To support some corrections, `NCO operators <http://nco.sourceforge.net/#Binaries>`_ must be installed.

