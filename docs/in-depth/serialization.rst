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
* Dumper: :py:func:`json.dumps`.

*****
JSON5
*****

* Loader: :py:func:`pyjson5.loads` or `json5.loads`_ as fallback.
* Dumper: :py:func:`pyjson5.dumps` or `json5.dumps`_ as fallback.

.. _json5.loads: https://github.com/dpranke/pyjson5
.. _json5.dumps: https://github.com/dpranke/pyjson5

***********
YAML (v1.2)
***********

* Loader: :py:func:`project_config.serializers.yaml.loads` (based on `ruamel.yaml`_).
* Dumper: :py:func:`project_config.serializers.yaml.dumps` (based on `ruamel.yaml`_).
* See `YAML supported types by version`_.

.. _YAML supported types by version: https://perlpunk.github.io/yaml-test-schema/schemas.html
.. _ruamel.yaml: https://yaml.dev/doc/ruamel.yaml/

*********
TOML (v1)
*********

* Loader: `tomlkit.parse`_.
* Dumper: `tomlkit.dumps`_.
* See the `TOML v1 specification`_.

.. _tomli.loads: https://github.com/hukkin/tomli#parse-a-toml-string
.. _tomllib.loads: https://docs.python.org/3.11/library/tomllib.html#tomllib.loads
.. _tomlkit.dumps: https://github.com/sdispater/tomlkit/blob/master/docs/quickstart.rst#modifying
.. _tomlkit.parse: https://github.com/sdispater/tomlkit/blob/master/docs/quickstart.rst#parsing
.. _TOML v1 specification: https://toml.io/en/v1.0.0

***
INI
***

* Loader: :py:func:`project_config.serializers.ini.loads`.
* Dumper: :py:func:`project_config.serializers.ini.dumps`.

************
Editorconfig
************

* Loader: :py:func:`project_config.serializers.editorconfig.loads`.
* Dumper: :py:func:`project_config.serializers.editorconfig.dumps`.

The `root` directive, if exists, will be added in an empty string key ``""`` object:

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

For Python files, the global namespace is exposed after executing the file in
a Python dictionary, including the key ``__file__`` with the script file path.

* Loader: :py:func:`project_config.serializers.python.loads`
* Dumper: :py:func:`project_config.serializers.python.dumps`

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
* Dumper: :py:func:`project_config.serializers.text.dumps`.

.. tabs::

   .. tab:: .gitignore

      .. code-block:: text

         bar
         baz

   .. tab:: object

      .. code-block:: json

         ["bar", "baz"]
