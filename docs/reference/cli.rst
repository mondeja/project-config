
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
