*****************************
Writing third party reporters
*****************************

.. seealso::

   :ref:`reference/cli:Reporting`

**project-config** discover third party reporters from plugin entrypoints
looking for modules in the entrypoints group ``project_config.reporters``,
so the first thing is to add the entrypoint to the group:

.. tabs::

   .. tab:: hatch

      .. code-block:: toml

         [project."entry-points"."project_config.plugins"]
         my_reporter = "package.subpackage.my_reporter_module"

   .. tab:: poetry

      .. code-block:: toml

         [tool.poetry.plugins."project_config.reporters"]
         my_reporter = "package.subpackage.my_reporter_module"

   .. tab:: setup.cfg

      .. code-block:: ini

         [options.entry_points]
         project_config.reporters =
             my_reporter = package.subpackage.my_reporter_module

   .. tab:: setup.py

      .. code-block:: python

         entry_points = {
             "project_config.reporters": [
                 "my_reporter = package.subpackage.my_reporter_module",
             ],
         }

The name of the entrypoint (`my_reporter` in the previous example)
is the name of the reporter that you must pass in the CLI option
:ref:`project-config---reporter` to use it.

Reporters module
================

A valid reporters module is made of two public classes which inherit from
:py:class:`project_config.reporters.base.BaseReporter`, one with ``ColorReporter``
(the colorized version of the reporter) as part of the name of the class
and other with ``Reporter``. If the user pass to the CLI ``--no-color``, the
black/white version of the reporter will be used, being the colorized the default.

.. tip::

   If you want a base class for the two reporters, you can name it starting
   with ``Base`` or ``_`` (making it private) and **project-config** will ignore
   it.

The class :py:class:`project_config.reporters.base.BaseReporter` is an abstract class
that enforces the following methods:

* :py:meth:`project_config.reporters.base.BaseReporter.generate_errors_report`
* :py:meth:`project_config.reporters.base.BaseReporter.generate_data_report`

For color reporters you may want to inherit from
:py:class:`project_config.reporters.base.BaseColorReporter`
and use the methods whose names start with ``format_`` to colorize certain
parts of the output.

See the built-in reporters at :ref:`reporters submodules <dev/reference/project_config.reporters:Submodules>`
and the :py:mod:`project_config.reporters.base` module for more information.

Testing reporters
=================

**project-config** comes with built-in `pytest fixtures`_ to
easily test reports generated from reporters. See
:py:mod:`project_config.tests.pytest_plugin.plugin`.

.. _pytest fixtures: https://docs.pytest.org/en/latest/explanation/fixtures.html
