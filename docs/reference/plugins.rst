#######
Plugins
#######

Plugins are the basic unit for rules application. Plugins defines
:bolditalic:`actions` which can be either :bolditalic:`verbs` or
:bolditalic:`conditionals`.

* :bolditalic:`conditionals` filter the execution of verbs in a rule. If all the conditionals of a rule returns ``true``, the verbs are executed. Conditionals are identified because they start with the prefix ``if``.
* :bolditalic:`verbs` execute actions against the files defined in the special ``files`` property of each rule. They act like asserters.

*********
inclusion
*********

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

.. rubric:: Example

Don't allow code blocks in RST documentation files:

* Bash is not a POSIX compliant shell.
* Pygments' JSON5 lexer is not implemented yet.

.. code-block:: js

   {
     rules: [
       files: ["docs/**/*.rst"],
       excludeContent: [
         ".. code-block:: bash",
         ".. code-block:: json5",
       ],
     ]
   }

.. versionadded:: 0.3.0

*********
existence
*********

Check existence of files.

ifFilesExist
============

Check if a set of files and/or directories exists.

It acceepts an array of paths. If a path ends with ``/`` character it is
considered a directory.

.. rubric:: Examples

If the directory `src/` exists, a `pyproject.toml` file must exist also:

.. code-block:: js

   {
     rules: [
       files: ["pyproject.toml"],
       ifFilesExist: ["src/"],
     ]
   }

If the file `.pre-commit-hooks.yaml` exists, must be declared as an array:

.. code-block:: js

   {
     rules: [
       files: [".pre-commit-hooks.yaml"],
       ifFilesExist: [".pre-commit-hooks.yaml"],
       JMESPathsMatch: [["type(@)", "array"]]
     ]
   }

.. versionadded:: 0.4.0

********
jmespath
********

`JMES paths`_ manipulation against files.

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

   .. deprecated:: 0.4.0

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

.. _JMES paths: https://jmespath.org
.. _JMESPath builtin functions: https://jmespath.org/proposals/functions.html#built-in-functions

JMESPathsMatch
==============

Compares a set of JMESPath expressions against results.

Object-serializes each file in the ``files`` property of the rule
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

crossJMESPathsMatch
===================

Compare a set of JMESPath expressions against results obtained
from querying other files against a expression.

Is the same verb as `JMESPathsMatch`_, but instead asserting against
a constant value, the result is asserted against the result of other
query against other or the same file.

As the value of each row takes an array with an existent file path as
the first item and the JMESPath expression as the second item.

.. rubric:: Example

The ``release`` field of a Sphinx configuration defined in a file
`docs/conf.py` must be the same that the version of the project metadata
defined in th file `pyproject.toml`, field ``tool.poetry.version``:

.. code-block:: js

   {
     rules: [
       {
         files: ["pyproject.toml"],
         crossJMESPathsMatch: [
           ["tool.poetry.metadata", ["docs/conf.py", "release"]],
         ],
         hint: "Versions of documentation and metadata must be the same"
       }
     ]
   }

.. versionadded:: 0.4.0

ifJMESPathsMatch
================

Compares a set of JMESPath expressions against results.

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
           "pyproject.toml": [
              ["tool.flakeheaven.inline_quotes", "double"],
            ],
         },
         JMESPathsMatch: [
           ["contains(keys(@), 'tool')", true],
           ["contains(keys(tool), 'black')", true],
         }
       }
     ]
   }

.. versionadded:: 0.1.0
