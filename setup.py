from setuptools import setup, find_packages

setup(name='timeaxis',
<<<<<<< HEAD
      version='3.4',
=======
      version='3.5',
>>>>>>> devel
      description='Check/Rewrite time axis of MIP NetCDF files.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/Prodiguer/cmip5-time-axis',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['netCDF4>=1.0.8', 'numpy>=1.8.1'],
      entry_points={'console_scripts': ['time_axis=timeaxis.timeaxis:run']},
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: System Administrators',
                   'Natural Language :: English',
                   'Operating System :: Unix',
                   'Programming Language :: Python :: 2.5',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Software Development :: Build Tools']
      )
