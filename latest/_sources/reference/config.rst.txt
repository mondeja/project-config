*************
Configuration
*************

Configuration must be defined in TOML_ format in one of the next files:

* `.project-config.toml`
* `pyproject.toml` (inside a ``[tool.project-config]`` table)
* A custom file passing ``-c``/``--config`` argument in the command line.

.. tip::

   You can use the ``project-config init`` command to initialize a minimal
   configuration and JSON5 style file.

   .. tabs::

      .. tab:: Initialization

         .. code-block:: sh

            project-config init

      .. tab:: .project-config.toml

         .. code-block:: toml

            style = ["style.json5"]
            cache = "5 minutes"

      .. tab:: style.json5

         .. code-block:: js

            {
              rules: [
                {
                  files: [".project-config.toml"],
                  JMESPathsMatch: [
                    ["type(style)", "array"],
                    ["op(length(style), '>', `0`)", true, "set(@, 'style', ['style.json5'])"],
                    ["type(cache)", "string", "set(@, 'cache', '5 minutes')"],
                    [
                      "regex_match('(\\d+ ((seconds?)|(minutes?)|(hours?)|(days?)|(weeks?)))|(never)$', cache)",
                      true,
                      "5 minutes",
                    ],
                  ]
                }
              ]
            }

.. _TOML: https://toml.io/en/

``style`` (`string` or `string[]`)
==================================

It is the unique mandatory field. At least one style with one rule must
be specified to run ``project-config``.

It can be a string or an array of strings, always pointing existent resources.
Valid resource types are:

* Local files with relative paths like `foo.json5` or `./bar.yaml`.
* Github schema URIs in the form ``gh://<user>/<project>(@tag)?/<path/to/file.ext>``
  like ``gh://mondeja/project-config-styles/python/version/min-37.json5``. The
  ``@`` syntax is used to pin a GIT reference (commit, tag, branch) and is optional,
  if is not specified the main branch of the repository will be used.
* Raw URLs like
  ``https://raw.githubusercontent.com/mondeja/project-config-styles/master/python/version/min-37.json5``.

The rules of the styles are applied in the same order that they are defined.

``cache`` (`string`)
====================

Cache expiration time for all online resources fetched. Default value is
``"5 minutes"``. Must follow the format ``cache = "<integer> <time-unit>"``.
Time unit can be one of these (plural or singular, it doesn’t matter):

* ``seconds / second``
* ``minutes / minute``
* ``hours / hour``
* ``days / day``
* ``weeks / week``

Also accept the next string to not use the cache at all.

* ``never``

.. tip::

   You can also disable the cache passing the CLI option ``--no-cache`` /
   ``--nocache`` or setting the ``PROJECT_CONFIG_USE_CACHE`` environment
   variable to ``"false"``.

.. seealso::

   You can use the command ``project-config show cache`` to output
   the location of project-config's cache directory.

   :doc:`./cli`

``cli`` (`object`)
==================

Configures the CLI execution. It avoids you to pass the same CLI arguments
to the **project-config** command.

.. seealso::

   :doc:`./cli`

``cli.rootdir`` (`string`)
--------------------------

Root directory of the project. Corresponds to the :ref:`project-config---rootdir`
optional CLI argument.

``cli.reporter`` (`string`)
---------------------------

Reporter to use. Corresponds to the ``NAME:FORMAT`` part of the
:ref:`project-config---reporter` optional CLI argument.

``cli.color`` (`boolean`)
-------------------------

Specifies if your want the output to be colored. Corresponds to the
:ref:`project-config---no-color` optional CLI argument.

``cli.colors`` (`object`)
-------------------------

Custom colors used in the output of the CLI. Corresponds to the ``color=``
argument of the :ref:`project-config---reporter` optional CLI argument.

``cli.only_hints`` (`boolean`)
------------------------------

Specifies if you want to only show the hints rather than the full error messages
if rules have them. As default disabled.

.. rubric:: Example

.. tabs::

   .. tab:: .project-config.toml

      .. code-block:: toml

         style = ["style.json5"]
         cache = "5 minutes"

         [cli]
         color = false
         reporter = "json"
         rootdir = "src"
         only_hints = true

   .. tab:: pyproject.toml

      .. code-block:: toml

         [tool.project-config]
         style = ["style.json5"]
         cache = "5 minutes"

         [tool.project-config.cli]
         color = false
         reporter = "json"
         rootdir = "src"
         only_hints = true
