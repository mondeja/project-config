************
Contributing
************

Development install
===================

.. code-block:: sh

   git clone https://github.com/mondeja/project-config
   cd project-config
   pip install hatch

Run tests
=========

.. code-block:: sh

   hatch run tests:unit
   # hatch run tests:all
   # hatch run tests:cov


Linting and formatting
======================

.. code-block:: sh

   hatch run style:lint


Build documentation
===================

.. code-block:: sh

   hatch run docs:build
   # hatch run docs:serve

Release
=======

You must have administrator permissions on the repository.

.. code-block:: sh

   version="$(hatch run bump <major/minor/patch>)"
   git add .
   git commit -m "Bump version"
   git push origin master
   git tag -a "v$version"
   git push origin "v$version"
