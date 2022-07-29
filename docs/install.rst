************
Installation
************

.. tabs::

   .. tab:: Python

      .. rubric:: pip

      .. code-block:: sh

         pip install project-config

      .. rubric:: poetry

      .. code-block:: sh

         poetry add project-config

   .. tab:: Node.js

      Requires Python >= 3.7 and `pip`_ installed.

      .. rubric:: npm

      .. code-block:: sh

         npm install -D python-project-config

      .. rubric:: yarn

      .. code-block:: sh

         yarn add -D python-project-config

   .. tab:: pre-commit

      .. rubric:: check

      .. code-block:: yaml

         - repo: https://github.com/mondeja/project-config
           rev: v0.7.6
           hooks:
             - id: project-config

      .. rubric:: fix

      .. code-block:: yaml

         - repo: https://github.com/mondeja/project-config
           rev: v0.7.6
           hooks:
             - id: project-config-fix

      .. seealso::

         `pre-commit.com`_

         .. _pre-commit.com: https://pre-commit.com

   .. tab:: MegaLinter plugin

      .. code-block:: yaml

         PLUGINS:
           - https://raw.githubusercontent.com/mondeja/project-config/v0.7.6/contrib/mega-linter-plugin-project-config/project-config.megalinter-descriptor.yml
         ENABLE_LINTERS:
           - PROJECT_CONFIG

      .. seealso::

         `MegaLinter`_

         .. _MegaLinter: https://megalinter.github.io

.. _pip: https://pypi.org/project/pip/
