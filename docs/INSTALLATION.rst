************
Installation
************

PanelPal can be installed as a docker. To install the application, follow the steps below:

* Clone the git repository

.. code-block:: bash

    git clone https://github.com/sch-sdgs/PanelPal.git

* Move into the PanelPal directory

.. code-block:: bash

    cd <path_to_PanelPal>

* Copy the database to a location on your machine. This creates a duplicate of the database to allow backups of the data
  outside the docker.

.. code-block:: bash

    cp resources/panel_pal.db <location_for_copy>

* Build the docker **N.B.** This can take some time

.. code-block:: bash

    docker build -t sdgsbinfx/panelpal:test .

* Run the docker

.. code-block:: bash

    docker run -p <free_port>:80 -v <path_to_local_copy_of_database>:/resources -t sdgsbinfx/panelpal:test

You can now navigate to PanelPal using the IP address for your machine, followed by a colon and the port you entered
when running the docker.

To install this on Snowball at SDGS, the following should be used:

* <location_for_copy> = /sdgs/databases/panelpal
* <free_port> = 86

The path to PanelPal if installed on port 86 on snowball is http://panelpal.sch.nhs.uk/