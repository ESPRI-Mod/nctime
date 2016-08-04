from setuptools import setup, find_packages

setup(name='nctime',
      version='3.8.0',
      description='Diagnoses NetCDF time axis.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/Prodiguer/nctimeaxis',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['netCDF4>=1.0.8', 'networkx==1.9', 'numpy>=1.8.1', 'nco>=0.0.2'],
      entry_points={'console_scripts': ['nctime=nctime.nctime:run']},
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
