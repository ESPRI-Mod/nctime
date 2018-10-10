.. _configuration:

Configuration
=============

``nctime`` works according to
`the configuration INI file(s) of the ESGF nodes <https://github.com/ESGF/config/tree/master/publisher-configs/ini>`_.

Location
********

On an ESGF node, the configuration directory containing those INI files is ``/esg/config/esgcet``, that is the default
for ``nctime``. In the case you are running ``nctime`` outside of an ESGF node, the directory gathering all ``.ini``
files has to be submitted using the ``-i`` option (see :ref:`usage`).

``esg.<project_id>.ini``
************************

Those INI files declare all facets and allowed values according to the Data Reference Syntax (DRS) and the controlled
vocabularies of the corresponding project. ``nctime`` especially use the filename format to deduce facet values.
Preset ``esg.<project_id>.ini`` files have been properly built by ESGF community for the following projects:

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

Those project INI files can be fetched from the official GitHub repository using the `esgfetchini` tool from the
`esgprep <http://esgf.github.io/esgf-prepare/fetchini.html>`_ Python toolbox.

Currently, ``nctime`` has been tested and supports CMIP5-like and CORDEX-like projects.
