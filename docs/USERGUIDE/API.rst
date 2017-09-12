****
API
****

The API has been created to allow the pipeline to access the panels and preferred transcripts held within the database.
There are five methods:

* Panel
* Virtual panel
* Intronic
* Gene
* Preftx

All methods return a JSON object. The result is split into two sections, the actual information returned and the
provenance details for the request. The details section of the return result contains the name and version of the object
that was returned to allow this to be recorded in the pipeline documents. The results list can then be parsed by the
pipeline to create the required text or BED file.

Panel
=====

The panel method will retrieve all regions for the panel with an extension of +/- 25 bp for each region in the panel.
The method requires the name of the panel and the version to eb retrieved. If the most recent version is required, this
argument can be "current", otherwise a specific number must be given.

The method returns a list of regions in dictionary format. each region object contains:

* chrom
* start
* end
* annotation

These elements can then be used to create the rows for the BED file. The regions are merged and sorted before being
added to the list and so can be processed sequentially to create the file.

Virtual Panel
=============

The virtual panel method will retrieve all regions for the specified virtual panel. The extension can be given as an
argument in this method; if it is not specified, it is assumed to be zero. This method requires the name and version of
the virtual panel. If the most recent version is to be returned, the version argument can be "current", otherwise a
specific number must be given.

The method returns a list of regions in dictionary format. each region object contains:

* chrom
* start
* end
* annotation

These elements can then be used to create the rows for the BED file. The regions are merged and sorted before being
added to the list and so can be processed sequentially to create the file.

Intronic
========

This method returns the +/- 5bp to +/- 25 bp co-ordinates for each region within a virtual panel. this method has been
designed to facilitate the coverage calculations performed within the pipeline. These regions have a minimum coverage
requirement of 18X rather than the 30X expected for exonic regions. The method requires the name and the version of the
virtual panel. If the most recent version is to be used the version argument can be "current", otherwise a specific
number must be given.

The method returns a list of regions in dictionary format. each region object contains:

* chrom
* start
* end
* annotation

These elements can then be used to create the rows for the BED file. The regions are merged and sorted before being
added to the list and so can be processed sequentially to create the file.

Gene
====

This method returns a BED file containing padded regions for a panel. This BED file is required for BAM and variant
calling filters within the diagnostic pipeline. The regions returned are for all exons for a gene +/- 1000 bp. This
allows intronic regions to still be included in the BAM file and prevents edge effects from impacting variant calling.

The method requires the name and the version of the panel. If the most recent version of the panel is required, the
version argument can be "current", otherwise a specific number must be given.

The method returns a list of regions in dictionary format. each region object contains:

* chrom
* start
* end
* annotation

These elements can then be used to create the rows for the BED file. The regions are merged and sorted before being
added to the list and so can be processed sequentially to create the file.

Preftx
======

The Preftx method returns the preferred transcripts for a specific project. The method requires the name of the project
and the preferred transcripts version to be returned. The version argument can be "current" if the most recent preferred
transcript selection is required. This method returns a list of key:value pairs that give the gene name and selected
accession number.