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
          rev: v0.4.0
          hooks:
            - id: project-config
