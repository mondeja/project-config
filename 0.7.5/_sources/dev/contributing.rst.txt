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
   poetry install
   pre-commit install
   poetry self add poetry-exec-plugin

Test
====

.. code-block:: sh

   poetry exec test
   # or `poetry exec t`

Show coverage report
--------------------

.. code-block:: sh

   poetry exec test:show

End to end tests
----------------

.. code-block:: sh

   poetry exec test:e2e

Lint
====

.. code-block:: sh

   poetry exec lint


Build documentation
===================

.. code-block:: sh

   poetry exec doc
   # or `poetry exec doc:show`

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
