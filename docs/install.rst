************
Installation
************

.. tabs::

   .. tab:: pip

      .. code-block:: bash

         pip install project-config

   .. tab:: poetry

      .. code-block:: bash

         poetry add project-config

   .. tab:: pre-commit

      .. code-block:: yaml

         - repo: https://github.com/mondeja/project-config
           rev: v0.7.0
           hooks:
             - id: project-config

   .. tab:: MegaLinter plugin

      .. code-block:: yaml

         PLUGINS:
           - https://raw.githubusercontent.com/mondeja/project-config/v0.7.0/contrib/mega-linter-plugin-project-config/project-config.megalinter-descriptor.yml
         ENABLE_LINTERS:
           - PROJECT_CONFIG
