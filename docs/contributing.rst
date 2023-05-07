.. _contributing:

======================
Contributing
======================

We are happy that you are thinking about contributing. 

For general information about contributing checkout Beeware_. Their materials are very good and align with our principles. The next sections contains technical details on how to contribute to Click, such as how to build the docs locally. 

Documentation Guidelines
============================
We are slowly rewriting our documentation to fall into four categories, tutorials, how-to guides, reference information, topics. If you are considering helping rewrite a section, please take a look at Diataxis_. 

How to contribute 
====================== 

Install 
------------------------------------------
#. Fork Click_ on github.
#. Clone project. 
    .. code-block:: sh 

        git clone https://github.com/<your_github_username>/click.git && cd ./click
#. Install python 3.8 in whatever manner works best for you. 
#. Install requirements and project in editable mode. 
    .. code-block:: sh 

        pip install -r ./requirements/dev.txt && pip install -e .

#. Install pre-commit hooks. 
    .. code-block:: sh 

        pre-commit install --install-hooks 

Run test suite locally 
--------------------------------------------

.. code-block:: sh

    pytest

Preview documentation locally
------------------------------------------- 

Use sphinx to build the docs: 

.. code-block:: sh

    sphinx-build ./docs ./_build

.. _Click: https://github.com/pallets/click/
.. _Pallets: https://github.com/click-contrib/
.. _Beeware: https://beeware.org/contributing/how/
.. _Diataxis: https://diataxis.fr/
