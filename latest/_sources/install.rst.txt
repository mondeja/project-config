************
Installation
************

.. tabs::

   .. tab:: Standalone

      .. rubric:: pip

      .. code-block:: bash

         pip install project-config

      .. rubric:: poetry

      .. code-block:: bash

         poetry add project-config

   .. tab:: pre-commit

      .. rubric:: check

      .. code-block:: yaml

         - repo: https://github.com/mondeja/project-config
           rev: v0.7.3
           hooks:
             - id: project-config

      .. rubric:: fix

      .. code-block:: yaml

         - repo: https://github.com/mondeja/project-config
           rev: v0.7.3
           hooks:
             - id: project-config-fix

   .. tab:: MegaLinter plugin

      .. code-block:: yaml

         PLUGINS:
           - https://raw.githubusercontent.com/mondeja/project-config/v0.7.3/contrib/mega-linter-plugin-project-config/project-config.megalinter-descriptor.yml
         ENABLE_LINTERS:
           - PROJECT_CONFIG
