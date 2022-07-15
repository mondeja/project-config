
******************
project-config CLI
******************

.. sphinx_argparse_cli::
   :module: project_config.__main__
   :func: build_main_parser
   :prog: project-config
   :title:

..
   FIXME: the optional arguments group is not added to toctree,
          see https://github.com/tox-dev/sphinx-argparse-cli/issues/48

.. rubric:: Commands

* ``project-config check`` - Check the styles of the current project.
* ``project-config fix`` - Fix the files of the current project.
* ``project-config init`` - Initialize a minimal style for the current project.
* ``project-config show config`` - Show the configuration.
* ``project-config show style`` - Show the collected styles merged into the final one.
* ``project-config show plugins`` - Show all available plugins with their actions.
* ``project-config show cache`` - Show cache directory location.
* ``project-config clean cache`` - Clean the persistent cache of remote collected sources.

.. tip::

   **project-config** CLI sets the environment variable ``PROJECT_CONFIG`` while
   is running.

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

Reporting
=========

**project-config** supports multiple formats for reporting. Currently,
the following reporters are supported:

* ``default`` - The default reporter, based on YAML but simplified.
* ``yaml`` - YAML reporter with flow style format.
* ``json`` - JSON reporter.
* ``toml`` - TOML reporter.
* ``table`` - Table reporters using `tabulate`_.

.. _tabulate: https://github.com/astanin/python-tabulate

When you pass a reporter with the :ref:`project-config---reporter` option, you
can specify the variant of the format with ``reporter:format``  syntax, for
example ``table:html`` will output the errors in an HTML table.

Additional third party reporters can be implemented as plugins,
see :ref:`dev/reporters:Writing third party reporters` for more information.

The reporter output affects the output of the next commands:

* ``project-config check``
* ``project-config fix``
* ``project-config show config``
* ``project-config show style``
* ``project-config show plugins``

.. note::

   Keep in mind that errors shown by ``check`` and ``fix`` commands are redirected
   to STDERR.

   Colorized output can't be serialized, so if you want to postprocess the report
   in the command line use always the :ref:`project-config---no-color` flag or set
   the environment variable ``NO_COLOR``.

Examples of usage
=================

Check the styles of the current project reporting in TOML format without
color and making all requests to remote sources:

.. code-block:: sh

   project-config check -r toml --no-color --no-cache

The installation of **project-config** from Python sources comes with
the `jmespath Python library`_, which includes the CLI tool ``jp.py``
that can be used to apply JMESPath queries to JSON reports produced by
**project-config**.

For example, to show the number of incorrect files detected by the
``check`` command (Unix only):

.. code-block:: sh

   project-config check -r json --no-color 2>&1 | jp.py 'length(keys(@))'

Show the number of rules defined in your styles after collecting all:

.. code-block:: sh

   project-config show style -r json --no-color 2>&1 | jp.py 'length(rules)'

Show the number of actions currently available:

.. code-block:: sh

   project-config show plugins -r json --no-color 2>&1 | jp.py 'length(*[])'

Show your styles after collecting all in YAML format:

.. code-block:: sh

   project-config show style -r yaml

Fix the styles for the current project:

.. code-block:: sh

   project-config fix

Initialize a minimal configuration:

.. code-block:: sh

   project-config init

Initialize a minimal configuration storing the configuration inside a `pyproject.toml` file:

.. code-block:: sh

   project-config init --config pyproject.toml

Initialize a minimal configuration storing the configuration in a custom file located
in a relative project root directory:

.. code-block:: sh

   project-config init --config styles-configuration.toml --rootdir my/subdir

.. _jmespath Python library: https://pypi.org/project/jmespath/
