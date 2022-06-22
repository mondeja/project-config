************
Contributing
************

Development install
===================

You need to install `poetry`_ >= 1.2.0 and `pre-commit`_ before.

.. code-block:: sh

   git clone https://github.com/mondeja/project-config
   cd project-config
   poetry install
   pre-commit install
   pip install --user poetry-exec-plugin

Test
====

.. code-block:: sh

   poetry exec test
   # or just `poetry exec t`

Lint
====

.. code-block:: sh

   poetry exec lint


Build documentation
===================

.. code-block:: sh

   poetry exec doc
   # or better: `poetry exec doc:show`

Release
=======

.. code-block:: sh

   version="$(poetry run bump <major/minor/patch>)"
   git add .
   git commit -m "Bump version"
   git push origin master
   git tag -a "v$version"
   git push origin "v$version"

.. _poetry: https://python-poetry.org/
.. _pre-commit: https://pre-commit.com/
