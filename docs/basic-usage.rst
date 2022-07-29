***********
Basic usage
***********

The minimal possible configuration depends on two files, the configuration
and one style file:

.. tabs::

   .. tab:: .project-config.toml

     .. code-block:: toml

        style = "foo.json"

   .. tab:: foo.json

     .. code-block:: json

        {
          "rules": [
            {
              "files": [".gitignore"],
              "includeLines": ["/dist/"]
            }
          ]
        }

This example enforces the existence of a `.gitignore` file which must
include a line with the content ``/dist/``.

The first time that you execute ``project-config check`` will raise an
error indicating the abcense of `.gitignore`:

.. code-block:: yaml

   .gitignore
     - Expected existing file does not exists rules[0].files[0]

If you create a `.gitignore` keeping it empty, the second time it will
warns indicating that the file does not include the line:

.. code-block:: yaml

   .gitignore
     - Expected line '/dist/' not found rules[0].includeLines[0]

If you include the line, it will not warn exiting with 0 code.

.. rubric:: Autofixing

This example is automatically fixable executing ``project-config fix``
when the file `.gitignore` is even unexistent.

.. code-block:: sh

   $ project-config fix
   .gitignore
     - (FIXED) Expected existing file does not exists rules[0].files[0]
     - (FIXED) Expected line '/dist/' not found rules[0].includeLines[0]

.. seealso::

   Output from real examples:

   .. tabs::

      .. tab:: project-config check

         .. image:: _static/img/project-config-check.png
            :target: _static/img/project-config-check.png

      .. tab:: project-config fix

         .. image:: _static/img/project-config-fix.png
            :target: _static/img/project-config-fix.png
