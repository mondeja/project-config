#####################
Objects serialization
#####################

Some plugins like :ref:`reference/plugins:jmespath` apply their
actions against object-serialized version of files. Also, the style
files itself parsed by **project-config** to execute the rules are
serialized to objects.

This is really convenient for configuration files because the most
common files formats like JSON, TOML or YAML can be converted into a
map (dictionary in Python, object in Javascript) to perform operations
against the structured nodes.

The serialization process of **project-config** converts strings to
Python dictionaries using loader functions depending on the format
of the files. The format is discovered, based mostly on file names,
using `identify`_.

.. _identify: https://github.com/pre-commit/identify

The next formats are currently supported:

****
JSON
****

* Loader: :py:func:`json.loads`.

*****
JSON5
*****

* Loader: :py:func:`pyjson5.loads` (if installed) or `json5.loads`_.

.. _json5.loads: https://github.com/dpranke/pyjson5

***********
YAML (v1.2)
***********

* Loader: :py:func:`project_config.serializers.yaml.loads` (based on `ruamel.yaml`_).
* See `YAML supported types by version`_.

.. _YAML supported types by version: https://perlpunk.github.io/yaml-test-schema/schemas.html
.. _ruamel.yaml: https://yaml.readthedocs.io/en/latest

*********
TOML (v1)
*********

* Loader: `tomli.loads`_ (Python < 3.11) or `tomllib.loads`_.
* See the `TOML v1 specification`_.

.. _tomli.loads: https://github.com/hukkin/tomli#parse-a-toml-string
.. _tomllib.loads: https://docs.python.org/3.11/library/tomllib.html#tomllib.loads
.. _TOML v1 specification: https://toml.io/en/v1.0.0

***
INI
***

* Loader: :py:func:`project_config.serializers.ini.loads`.

************
Editorconfig
************

* Loader: :py:func:`project_config.serializers.editorconfig.loads`.

The `root` directive, if exists, will be added in a ``""`` object:

.. tabs::

   .. tab:: .editorconfig

      .. code-block:: ini

         root = true

         [*]
         end_of_line = lf
         charset = utf-8
         indent_style = space
         trim_trailing_whitespace = true

   .. tab:: object

      .. code-block:: json

         {
           "": {
             "root": true
           },
           "*": {
             "end_of_line": "lf",
             "charset": "utf-8",
             "indent_style": "space",
             "trim_trailing_whitespace": true
           }
         }

******
Python
******

For Python files, the global namespace exposed is serialized after
executing them.

* Loader: :py:func:`project_config.serializers.python.loads`

.. tabs::

   .. tab:: foo.py

      .. code-block:: python

         bar = "baz"

   .. tab:: object

      .. code-block:: json

         {
           "bar": "baz"
         }

.. tip::

   **project-config** CLI sets the environment variable ``PROJECT_CONFIG``
   while is running, which is useful if you want to expose the global namespaces
   of scripts only when the tool is running.

****
Text
****

Fallback for all serialized files. Just converts the string to an array
of lines, excluding line endings.

* Loader: :py:func:`project_config.serializers.text.loads`.

.. tabs::

   .. tab:: foo.txt

      .. code-block:: text

         bar
         baz

   .. tab:: object

      .. code-block:: json

         ["bar", "baz"]
