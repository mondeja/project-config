************
Contributing
************

Development install
===================

.. code-block:: sh

   git clone https://github.com/mondeja/project-config
   cd project-config
   pip install hatch

Testing
=======

.. code-block:: sh

   hatch run tests:unit
   # or `hatch run tests:all`

Show coverage report
--------------------

.. code-block:: sh

   hatch run tests:cov

End to end tests
----------------

.. code-block:: sh

   hatch run tests:all

Linting
=======

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

   version="$(hatch run bump <major/minor/patch>)"
   git add .
   git commit -m "Bump version"
   git push origin master
   git tag -a "v$version"
   git push origin "v$version"
