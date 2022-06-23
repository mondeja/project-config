
******************
project-config CLI
******************

.. sphinx_argparse_cli::
   :module: project_config.__main__
   :func: _build_main_parser
   :prog: project-config
   :title:

..
   FIXME: the optional arguments group is not added to toctree,
          see https://github.com/tox-dev/sphinx-argparse-cli/issues/48

.. rubric:: Commands

* ``project-config check`` - Check the styles of the current project.
* ``project-config show config`` - Show the configuration.
* ``project-config show style`` - Show the collected styles merged into the final one.
* ``project-config show cache`` - Show cache directory location.
* ``project-config clean cache`` - Clean the persistent cache of remote collected sources.

..
   .. sphinx_argparse_cli::
      :module: project_config.__main__
      :func: _build_main_parser
      :prog: project-config

      ..
         FIXME: see https://github.com/tox-dev/sphinx-argparse-cli/issues/47

      ***********************************
      project-config positional arguments
      ***********************************

      * ``project-config check`` Check the styles of the current project.
      * ``project-config show config`` Show the configuration.
      * ``project-config show style`` Show the collected styles merged into the final one.
      * ``project-config show cache`` Show cache directory location.
      * ``project-config clean cache`` Clean the persistent cache of remote collected sources.

Reporting errors
================

**project-config** supports multiple formats for reporting. Currently,
the following reporters are supported:

* ``default`` - The default reporter, based on YAML but simplified.
* ``yaml`` - YAML reporter with flow style format.
* ``json`` - JSON reporter.
* ``toml`` - TOML reporter.
* ``table`` - Table reporters using `tabulate`_.

.. _tabulate: https://github.com/astanin/python-tabulate

When you pass a reporter with the ``-r`` / ``--reporter`` option, you can
specify the variant of the format with ``reporter:format``  syntax, for example
``table:html`` will output the errors in an HTML table.

The reporter output affects the output of the next commands:

* ``project-config check``
* ``project-config show config``
* ``project-config show style``

Additional third party reporters can be implemented as plugins,
see :ref:`dev/reporters:Writing third party reporters` for more information.
