************
Contributing
************

Development install
===================

You need to install the latest version of `poetry`_ >= 1.2.0 and
`pre-commit`_ before.

.. code-block:: sh

   git clone https://github.com/mondeja/project-config
   cd project-config
   pip install hatch

Testing
=======

.. code-block:: sh

   hatch run tests:unit
   # or `has run tests:e2e`

Show coverage report
--------------------

.. code-block:: sh

   hatch run tests:cov

End to end tests
----------------

.. code-block:: sh

   hatch run tests:e2e

Lint
====

.. code-block:: sh

   hatch run style:lint


Build documentation
===================

.. code-block:: sh

   hatch run docs:build
   # or `hatch run docs:serve`

Release
=======

You must have administrator permissions on the repository.

.. code-block:: sh

   version="$(poetry run bump <major/minor/patch>)"
   git add .
   git commit -m "Bump version"
   git push origin master
   git tag -a "v$version"
   git push origin "v$version"

.. _poetry: https://python-poetry.org/
.. _pre-commit: https://pre-commit.com/
