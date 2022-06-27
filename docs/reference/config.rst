*************
Configuration
*************

Configuration must be defined in TOML_ format in one of the next files:

* `.project-config.toml`
* `pyproject.toml` (inside a ``[tool.project-config]`` table)
* A custom file passing ``-c``/``--config`` argument in the command line.

``style`` (`string` or `string[]`)
==================================

It is the unique mandatory field. At least one style with one rule must
be specified to run ``project-config``.

It can be a string or an array of strings, always pointing existent resources.
Valid resource types are:

* Local files with relative paths like `foo.json5` or `./bar.yaml`.
* Github schema URIs in the form `gh://<user>/<project>(@tag)?/<path/to/file.ext>`
  like `gh://mondeja/project-config-styles/python/version/min-37.json5`. The
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

Also accepts the next string to not use the cache at all.

* ``never``

.. _TOML: https://toml.io/en/

.. tip:: Temporally disabling cache

   You can also disable the cache passing the CLI option ``--no-cache`` /
   ``--nocache`` or setting the ``PROJECT_CONFIG_USE_CACHE`` environment
   variable to ``"false"``.
