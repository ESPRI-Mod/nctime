#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from nctime.utils.constants import VERSION

setup(name='nctime',
      version=VERSION,
      description='Diagnoses NetCDF time axis.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/Prodiguer/nctime',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['netCDF4==1.4.0',
                        'netcdftime==1.0.0a2',
                        'networkx==2.1',
                        'numpy==1.14.2',
                        'nco==0.0.3',
                        'esgconfigparser==0.1.17',
                        'fuzzywuzzy>=0.16.0'],
      entry_points={'console_scripts': ['nctime=nctime.nctime:main']},
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: System Administrators',
                   'Natural Language :: English',
                   'Operating System :: Unix',
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Software Development :: Build Tools']
      )
