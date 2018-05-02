.. _configuration:

Configuration
=============

``nctime`` works according to
`the configuration INI file(s) of the ESGF nodes <https://acme-climate.atlassian.net/wiki/x/JADm>`_.

Location
********

On an ESGF node, the configuration directory containing those INI files is ``/esg/config/esgcet``, that is the default
for ``nctime``. In the case you are running ``nctime`` outside of an ESGF node, the directory gathering all ``.ini``
files has to be submitted using the ``-i`` option (see :ref:`usage`).

``esg.ini``
***********

This INI file gathers all required information to configure the datanode regarding to data publication (e.g.,
PostgreSQL access, THREDDS configuration, etc.).

The only configuration in this section is to define the checksum client and checksum
type under the ``[default]`` section. Edit the file to set the Shell command line to use (default is ``sha256sum``).

.. code-block:: ini

    [default]
    checksum = sha256sum | SHA256

.. note:: If ``esg.ini`` is unfound, the default is SHA256.

``esg.<project_id>.ini``
************************

Those INI files declare all facets and allowed values according to the Data Reference Syntax (DRS) and the controlled
vocabularies of the corresponding project. Preset ``esg.<project_id>.ini`` files have been properly built by
ESGF community for the following projects:

 * CMIP6
 * CMIP5
 * CORDEX
 * CORDEX-Adjust
 * EUCLIPSE
 * GeoMIP
 * input4MIPs
 * obs4MIPs
 * PMIP3
 * LUCID
 * PRIMAVERA
 * TAMIP
 * ISIMIP-FT

Currently, ``nctime`` has been tested and supports CMIP5-like and CORDEX-like projects.
