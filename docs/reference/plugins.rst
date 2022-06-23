#######
Plugins
#######

Plugins are the basic unit for rules application. Plugins defines
:bolditalic:`actions` which can be either :bolditalic:`verbs` or
:bolditalic:`conditionals`.

* :bolditalic:`conditionals` filter the execution of verbs in a rule. If all the conditionals of a rule returns ``true``, the verbs are executed. Conditionals are identified because they start with the prefix ``if``.
* :bolditalic:`verbs` execute actions against the files defined in the special ``files`` property of each rule. They act like asserters.

*******
include
*******

Plain content inclusion management.

includeLines
============

Check that the files include all lines passed as argument.

If the files don't include all lines specified as argument,
it will raise a checking error. Newlines are ignored, so they
should not be specified.

.. rubric:: Example

.. code-block:: js

   {
     rules: [
       files: [".gitignore"],
       includeLines: ["venv*/", "/dist/"]
     ]
   }

.. versionadded:: 0.1.0

ifIncludeLines
==============

Conditional to exclude rule only if some files include a set of lines.

If one file don't include all lines passed as parameter,
the rule will be ignored.

Accepts an object mapping files to lines that must be included in order
to execute the rule.

.. rubric:: Example

If the license defined in the `LICENSE` file is BSD-3, ``tool.poetry.license``
must correspont:

.. code-block:: js

   {
     rules: [
       files: ["pyproject.toml"],
       ifIncludeLines: {
         LICENSE: ["BSD 3-Clause License"],
       },
       JMESPathsMatch: [
         ["tool.poetry.license", "BSD-3-License"],
       ]
     ]
   }

.. versionadded:: 0.1.0

excludeContent
==============

Check that the files do not include certain content.

The specified partial contents can match multiple lines
and line ending characters.



********
jmespath
********

JMES paths manipulation against files.

The actions of this plugin operates against object-serialized versions
of files, so only files that can be serialized can be targetted (see
:ref:`in-depth/serialization:Objects serialization`).

You can use in expressions all `JMESPath builtin functions`_ plus a set of
convenient functions defined by the plugin internally:

.. function:: regex_match(pattern: str, string: str) -> bool

   Match a regular expression against a string using the Python's built-in
   :py:func:`re.match` function.

   .. versionadded:: 0.1.0

.. function:: regex_matchall(pattern: str, strings: list[str]) -> bool

   Match a regular expression against a set of strings defined in an array
   using the Python's built-in :py:func:`re.match` function.

   .. versionadded:: 0.1.0

.. function:: regex_search(pattern: str, string: str) -> list[str]

   Search using a regular expression against a string using the Python's
   built-in :py:func:`re.search` function. Returns all found groups in an
   array or an array with the full match as the unique item if no groups
   are defined. If no results are found, returns an empty array.

   .. versionadded:: 0.1.0

.. function:: op(source: type, operation: str, target: type) -> bool

   Applies the operator `operator` between the two values using the operators
   for two values defined in :py:mod:`op`. The next operators are available:

   * ``<``: :py:func:`operator.lt`
   * ``<=``: :py:func:`operator.le`
   * ``==``: :py:func:`operator.eq`
   * ``!=``: :py:func:`operator.ne`
   * ``>=``: :py:func:`operator.ge`
   * ``>``: :py:func:`operator.gt`
   * ``is``: :py:func:`operator.is_`
   * ``is_not``: :py:func:`operator.is_not`
   * ``is-not``: :py:func:`operator.is_not`
   * ``is not``: :py:func:`operator.is_not`
   * ``isNot``: :py:func:`operator.is_not`
   * ``+``: :py:func:`operator.add`
   * ``&``: :py:func:`operator.and_`
   * ``and``: :py:func:`operator.and_`
   * ``//``: :py:func:`operator.floordiv`
   * ``<<``: :py:func:`operator.lshift`
   * ``%``: :py:func:`operator.mod`
   * ``*``: :py:func:`operator.mul`
   * ``@``: :py:func:`operator.matmul`
   * ``|``: :py:func:`operator.or_`
   * ``or``: :py:func:`operator.or_`
   * ``**``: :py:func:`operator.pow`
   * ``>>``: :py:func:`operator.rshift`
   * ``-``: :py:func:`operator.sub`
   * ``/``: :py:func:`operator.truediv`
   * ``^``: :py:func:`operator.xor`
   * ``count_of``: :py:func:`operator.countOf`
   * ``count of``: :py:func:`operator.countOf`
   * ``count-of``: :py:func:`operator.countOf`
   * ``countOf``: :py:func:`operator.countOf`
   * ``index_of``: :py:func:`operator.indexOf`
   * ``index of``: :py:func:`operator.indexOf`
   * ``index-of``: :py:func:`operator.indexOf`
   * ``indexOf``: :py:func:`operator.indexOf`

   .. versionadded:: 0.1.0

.. _JMESPath builtin functions: https://jmespath.org/proposals/functions.html#built-in-functions

JMESPathsMatch
==============

Compares a set of JMESPath expression against results.

JSON-serializes each file in the ``files`` property of the rule
and executes each expression given in the first item of the
tuples passed as value. If a result don't match, report an error.

.. rubric:: Example

The `.editorconfig` file must have the next content:

.. code-block:: ini

   root = true

   [*]
   end_of_line = lf
   charset = utf-8
   indent_style = space
   trim_trailing_whitespace = true

.. code-block:: js

   {
     rules: [
       {
         files: [".editorconfig"],
         JMESPathsMatch: [
           ['"".root', true],
           ['"*".end_of_line', "lf"],
           ['"*".indent_style', "space"],
           ['"*".charset', "utf-8"],
           ['"*".trim_trailing_whitespace', true],
         ],
       }
     ]
   }

.. versionadded:: 0.1.0


ifJMESPathsMatch
================

Compares a set of JMESPath expression against results.

JSON-serializes each file in the ``ifJMESPathsMatch`` property
of the rule and executes each expression given in the first item of the
tuples passed as value for each file. If a result don't match,
skips the rule.

.. rubric:: Example

If ``inline-quotes`` config of flake8 is defined to use double quotes,
Black must be configured as the formatting tool in ``pyproject.toml``:

.. code-block:: js

   {
     rules: [
       {
         files: ["pyproject.toml"],
         ifJMESPathsMatch: {
           "pyproject.toml": [["tool.flakeheaven.inline_quotes", "double"]],
         },
         JMESPathsMatch: [
           ["contains(keys(@), 'tool')", true],
           ["contains(keys(tool), 'black')", true],
         }
       }
     ]
   }

.. versionadded:: 0.1.0
