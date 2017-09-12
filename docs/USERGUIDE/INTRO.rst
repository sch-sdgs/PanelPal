###########
The Jargon
###########

These are some of the main definitions associated with PanelPal. They will be used throughout this document, if there
is a term or phrase that you are unsure of and is not listed here please email the `bioinformatics`_ team.

.. _bioinformatics: mailto:matthewparker24+lzj6vkpuibpnivi6nsog@boards.trello.com?Subject=#PanelPal%20%20Help

Projects
========

Projects are used to group panels that belong to the same service. Each project is associated with users that are
allowed to edit the panels and virtual panels within the project. Projects also contain the preferred transcripts
associated with each service.

Panels
======

Panels reflect the regions that are contained within the probe set used for amplification fo the target regions. The
panels contain all regions that we are able to capture during the sequencing.

Virtual Panels
===============

Virtual panels are a subset of a particular panel. The regions included in the virtual panel **MUST** be included in the
parent panel. These panels are used to filter results to a region of interest that is associated with a specific
phenotype or disorder.

Preferred Transcripts
======================

Preferred transcripts are selected for each gene within a project. This means that the preferred transcript for a gene
is the same across all panels within a project. The preferred transcript for each gene is used for annotation of
variants within the diagnostic pipeline.

.. _make-live:

Make Live
=========

When a panel etc. is made it is not immediately available for use in service. This is to allow the gradual
development of panels and prevent incomplete data being used in the diagnostic pipeline. When a panel is ready to be
used in the pipeline it can be "made live" which means the version number increases and the changes are incorporated
into the version used in service. This concept applies to panels, virtual panels and preferred transcripts.

.. _upcoming:

Upcoming
========

If something is referred to as upcoming, it means that it has been changed in the next version of the panel or preferred
transcript list

.. _versions:

Versions
========

Panels are versioned incrementally with a single integer. When a panel is first created it is given a version number of
zero. This means that there are no live versions of the panel that can be accessed by the pipeline. Once a panel is
first made live, it moves to version one and this number increases every time a panel is "made live" following changes.

Virtual panels are versioned according to the virtual panel and the parent panel. The version number is formatted in the
following way:

*<panel version>*\ **.**\ *<virtual panel version>*

When changes are made to the virtual panel, the number after the decimal point is increased.

If changes have been made to the parent panel, the number before the decimal point will change. In this case the version
number of the virtual panel will change to
*<new panel version>*\ **.1**
so that the changes to the broad panel are applied when used in the pipeline. This is important for reanalysis as
regions that have been added to the parent panel will not be available in the BAM file and regions that have been
removed will appear as gaps.