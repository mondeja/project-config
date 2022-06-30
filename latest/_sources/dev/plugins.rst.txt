***************************
Writing third party plugins
***************************

.. seealso::

   :doc:`../reference/plugins`

**project-config** discover third party plugins from plugin entrypoints
looking for classes in the entrypoints group ``project_config.plugins``,
so the first thing is to add the entrypoint to the group:

.. tabs::

   .. tab:: poetry

      .. code-block:: toml

         [tool.poetry.plugins."project_config.plugins"]
         my_plugin = "package.subpackage.my_plugin_module:PluginClass"

   .. tab:: setup.cfg

      .. code-block:: ini

         [options.entry_points]
         project_config.plugins =
             my_plugin = package.subpackage.my_plugin_module:PluginClass

   .. tab:: setup.py

      .. code-block:: python

         entry_points = {
             "project_config.plugins": [
                 "my_plugin = package.subpackage.my_plugin_module:PluginClass",
             ],
         }

The name of the entrypoint (``my_plugin`` in the previous example)
is the name of the plugin, the one that must be defined in :ref:`style-plugins`
if the style need it.

Plugin class
============

A valid plugin class must implement actions, which must be public static
methods. For example:

.. code-block:: python

   from typing import Any
   from project_config import Tree, Rule, Results

   class PluginClass:
       @staticmethod
       def verb(  # any public method that do not start with 'if' is a verb
           value: Any,
           tree: Tree,
           rule: Rule,
       ) -> Results:
           ...

       @staticmethod
       def ifConditional(  # a conditional starts with 'if'
           value: Any,
           tree: Tree,
           rule: Rule,
       ) -> Results:
           ...

.. function:: action(value: typing.Any, tree: project_config.tree.Tree, rule: project_config.types.Rule) -> project_config.types.Results

   Action definition.

   :param value: Value that takes the action. It could be of any type, it depends to the action.
   :type value: typing.Any
   :param tree: Tree of files and directories that takes the action in the ``files`` property of the rule.
   :type tree: :py:class:`project_config.tree.Tree`
   :param rule: Complete rule dictionary in which the action is being executed.
   :type rule: :py:class:`project_config.types.Rule`

   :yield: Checking results.
   :rtype: :py:class:`project_config.types.Results`

Results
-------

Each action must yield results, which are tuples of two items,
defined next as `result type` - `result value`:

* ``Error`` - Checking error, a dictionary (optionally but recommendably typed as :py:class:`project_config.types.ErrorDict`) which must contains the required keys ``message`` (error message shown in the report) and ``definition`` (definition in which the error has been thrown) and an optional key ``file`` (file for which the error has been thrown). If raised from conditionals their behaviour is the same that raising an ``InterruptingError``.
* ``InterruptingError`` - The same as a checking error, but this type of error will stop the execution of the subsequent rules during the checking. Useful if the user has passed some unexpected value that could lead to an invalid context in some later rule.

Additionally, conditionals can yield result values, which
define if the verbs of the rule should be executed or not.

* ``ResultValue`` - A boolean. When a conditional yields it, the execution of the conditional is terminated and, if the yielded value is ``False``, the execution of the verbs of the rule are skipped. If no result values are yielded by a conditional, the verbs of the rule are always executed as if the conditional would returned ``True``.

You must import these variables from ``project_config`` because their
values can change between versions:

.. code-block:: python

   from project_config import Error, InterruptingError, ResultValue

.. seealso::

   The best way to learn the most common patterns to write plugins
   is checking the source code of the simplest built-in plugins:

   * :py:class:`project_config.plugins.include.IncludePlugin`
   * :py:class:`project_config.plugins.jmespath.JMESPathPlugin`


Testing plugins
===============

**project-config** comes with a built-in `pytest fixture`_ to
easily test plugin actions. See
:py:mod:`project_config.tests.pytest_plugin.plugin`.

.. _pytest fixture: https://docs.pytest.org/en/latest/explanation/fixtures.html
