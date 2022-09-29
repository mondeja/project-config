#######
Plugins
#######

Plugins are the providers of the basic units for the application of rules,
defining :bolditalic:`actions` which can be either :bolditalic:`verbs` or
:bolditalic:`conditionals`.

* :bolditalic:`conditionals` filter the execution of verbs in a rule. If all
  the conditionals of a rule returns ``true``, the verbs are executed.
  Conditionals are identified because they start with the prefix ``if``.
* :bolditalic:`verbs` execute actions against the files defined in the
  special ``files`` property of each rule. They act like asserters.

*********
inclusion
*********

Files content inclusion management.

includeLines
============

Check that the files include all lines passed as argument.

If the files don't include all lines specified as argument,
it will raise a checking error. Newlines are ignored, so they
should not be specified.

.. rubric:: Examples

.. tabs::

   .. tab:: Automatic inclusion

      Appends lines not already present in the file to the end.

      .. code-block:: js

         {
           rules: [
             files: [".gitignore"],
             includeLines: ["venv*/", "/dist/"]
           ]
         }

   .. tab:: Manual edition

      You can define manually a JMESPath fix query if the line is an array
      with the line and the fix query as items:

      .. code-block:: js

         {
           rules: [
             {
               files: [".gitignore"],
               hint: "The line 'dist/' must be included in .gitignore",
               includeLines: [
                 // Include all the lines which value is not a set of variants of `dist/`
                 // and append the line `dist/` to the end of the file
                 ["dist/", "op([?!contains(['/dist/', 'dist', 'dist/'], @)], '+', ['dist/'])"],
                 "__pycache__/",
               ]
             }
           ]
         }

      The returned value of the JMESPath fix query will be the new content
      of the file, an array with a ``'\n'.join(lines)`` transformation of the
      array of strings that represent the lines of the file.

.. versionadded:: 0.1.0

.. versionchanged:: 0.7.0

   Accept arrays of ``[line, fixer_query]`` as items of the array
   to edit manually the files using JMESPath queries.

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
and line ending characters. It just raises errors if the passed
contents are substrings of each file content.

.. rubric:: Example

.. include:: ../_examples/011-replace-codeblocks-langs/README.rst
   :parser: rst
   :start-line: 3

.. include:: ../_examples/011-replace-codeblocks-langs/style.json5
   :literal:

.. versionadded:: 0.3.0

.. versionchanged:: 0.7.0

   Accepts an array ``['content-to-exclude', fixer-query]`` for each item
   in the array to perform editions in the file if the content is found.

*********
existence
*********

Check existence of files.

ifFilesExist
============

Check if a set of files and/or directories exists.

Accepts an array of paths. If a path ends with ``/`` character it is
considered a directory.

.. rubric:: Examples

.. tabs::

   .. tab:: If directory exists

      If the directory `src/` exists, a `pyproject.toml` file must exist also:

      .. code-block:: js

         {
           rules: [
             files: ["pyproject.toml"],
             ifFilesExist: ["src/"],
           ]
         }

   .. tab:: If file exists

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

.. rubric:: Standard JMESPath functions

The next functions extends those functions that the official JMESPath library
has accepted and are compatible, but they offer some extra features:

.. function:: starts_with(search: str, prefix: str[, start: int=0[, end: int=-1]]) -> bool

   Return ``true`` if string starts with the prefix, otherwise return ``false``.
   The argument ``prefix`` can also be an array of prefixes to look for.
   With optional ``start``, test string beginning at that position.
   With optional ``end``, stop comparing string at that position.

   In the official implementation of JMESPath, the ``start`` and ``end``
   parameters are not included and ``prefix`` can only be a string.

   .. versionadded:: 0.1.0

   .. versionchanged:: 0.7.6

      * Added ``start`` and ``end`` parameters.
      * Added support for ``prefix`` to be an array of prefixes.

.. function:: ends_with(search: str, suffix: str[, start: int=0[, end: int=-1]]) -> bool

   Return ``true`` if the string ends with the specified suffix, otherwise
   return ``false``. The argument ``suffix`` can also be a tuple of suffixes
   to look for. With optional ``start``, test beginning at that position.
   With optional ``end``, stop comparing at that position.

   In the official implementation of JMESPath, the ``start`` and ``end``
   parameters are not included and ``suffix`` can only be a string.

   .. versionadded:: 0.1.0

   .. versionchanged:: 0.7.6

      * Added ``start`` and ``end`` parameters.
      * Added support for ``prefix`` to be an array of prefixes.

.. rubric:: Regex functions

All functions whose name start with ``regex_`` are regex functions, which
always takes the regex to apply as the first parameter following the Python's
`regex standard library`_ syntax.

.. function:: regex_match(pattern: str, string: str[, flags: int=0]) -> bool

   Match a regular expression against a string using the Python's built-in
   :py:func:`re.match` function.

   .. versionadded:: 0.1.0

   .. versionchanged:: 0.5.0

      Allow to pass ``flags`` optional argument as an integer.

.. function:: regex_matchall(pattern: str, strings: list[str]) -> bool

   Match a regular expression against a set of strings defined in an array
   using the Python's built-in :py:func:`re.match` function.

   .. versionadded:: 0.1.0

   .. deprecated:: 0.4.0

.. function:: regex_search(pattern: str, string: str[, flags: int=0]) -> list[str]

   Search using a regular expression against a string using the Python's
   built-in :py:func:`re.search` function. Returns all found groups in an
   array or an array with the full match as the unique item if no groups
   are defined. If no results are found, returns an empty array.

   .. versionadded:: 0.1.0

   .. versionchanged:: 0.5.0

      Allow to pass ``flags`` optional argument as an integer.

.. function:: regex_sub(pattern: str, repl: str, string: str[, count: int=0[, flags: int=0]]) -> str

   Replace using a regular expression against a string using the Python's
   built-in :py:func:`re.sub` function.

   .. versionadded:: 0.5.0

.. function:: regex_escape(pattern: str) -> str

   Escape a regular expression pattern using the Python's built-in :py:func:`re.escape`
   function.

   .. versionadded:: 0.7.5

.. seealso::

   :ref:`Example of regex_match() and rootdir_name()<examples:Assert root directory name>`.

.. _regex standard library: https://docs.python.org/3/library/re.html


.. rubric:: Utility functions

.. function:: os() -> str

   Return the result of the Python's variable `sys.platform`_.

   .. versionadded:: 0.7.0

.. function:: getenv(envvar: str) -> str

   Return the value of an environment variable.

   .. versionadded:: 0.8.0

.. function:: setenv(envvar: str, value: str | None) -> dict

   Set the value of an environment variable. If you set the value
   to ``null``, the environment variable will be removed.

   Return the updated environment object.

   .. versionadded:: 0.8.0

.. function:: rootdir_name() -> str

   Returns the name if the root directory of the project, that will be the
   current working directory or other that could be either passed in
   :ref:`project-config---rootdir` CLI option or defined in ``cli.rootdir``
   :doc:`configuration option <./config>`.

   .. versionadded:: 0.6.0

.. function:: op(source: any, operation: str, target: any[, operation: str, target: any]...) -> any

   Apply the operator ``operation`` between the two values ``source`` and ``target``
   using the operators for two values defined in the module :py:mod:`op`.

   The next operators are available:

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

   If ``source`` and ``target`` are both of type array and the operator
   is one of the next ones, the arrays are converted to
   :external:py:class:`set` before applying the operator:

   * ``<``: :py:func:`operator.lt`
   * ``<=``: :py:func:`operator.le`
   * ``>=``: :py:func:`operator.ge`
   * ``>``: :py:func:`operator.gt`
   * ``&``: :py:func:`operator.and_`
   * ``and``: :py:func:`operator.and_`
   * ``|``: :py:func:`operator.or_`
   * ``or``: :py:func:`operator.or_`
   * ``-``: :py:func:`operator.sub`
   * ``^``: :py:func:`operator.xor`

   .. rubric:: Example

   The next example checks that the configuration field ``tool.isort.sections``
   is a superset or equal to the array of strings
   ``['STDLIB', 'THIRDPARTY', 'FIRSTPARTY', 'LOCALFOLDER']`` appyling
   the operator ``<=``.

   These comparations are easier to do than checking every item in the array
   with the built-in JMESPath function ``contains()``.

   .. code-block:: js

      {
        rules: [
          {
            files: ["pyproject.toml"],
            JMESPathsMatch: [
              ["type(tool.isort)", "object"],
              ["type(tool.isort.sections)", "array"],
              [
                "op(['STDLIB', 'THIRDPARTY', 'FIRSTPARTY', 'LOCALFOLDER'], '<=', tool.isort.sections)",
                true,
              ],
            ],
          },
        ],
      }

   You can pass multiple operators and values after the ``target`` argument
   chaining the operation with multiple operators. For example:

   .. code-block:: text

      op(`5`, '+', `3`, '-', `4`)

   .. versionadded:: 0.1.0

   .. versionchanged:: 0.4.0

      Convert to :external:py:class:`set` before applying operators if both
      arguments are arrays.

   .. versionchanged:: 0.7.4

      Multiple optional operator and values can be passed as positional arguments.

.. function:: shlex_split(cmd_str: str) -> list

   Split a string using the Python's built-in function :py:func:`shlex.split`.

   .. versionadded:: 0.4.0

.. function:: shlex_join(cmd_list: list[str]) -> str

   Join a list of strings using the Python's built-in function :py:func:`shlex.join`.

   .. versionadded:: 0.4.0

.. function:: round(number: float[, precision: int]) -> float

   Round a number to a given precision using the Python's built-in function
   :external:py:func:`round`.

   .. versionadded:: 0.5.0

.. function:: range([start: float,] stop: float[, step: float]) -> list

   Return an array of numbers from ``start`` to ``stop`` with a step of ``step``
   casting the result of the constructor :external:py:class:`range` to an array.

   .. versionadded:: 0.5.0

.. function:: count(value: str | list, sub: any[, start: int[, end: int]]) -> int

   Return the number of occurrences of ``sub`` in ``value`` using :py:meth:`str.count`.
   If ``start`` and ``end`` are given, return the number of occurrences between
   ``start`` and ``end``.

   .. versionadded:: 0.5.0

.. function:: find(string: str | list, sub: any[, start: int[, end: int]]) -> int

   Return the lowest index in ``value`` where subvalue ``sub`` is found.
   If ``start`` and ``end`` are given, return the number of occurrences between
   ``start`` and ``end``. If not found, ``-1`` is returned.

   If ``value`` is a string it uses internally the Python's built-in function
   :py:meth:`str.find`. If ``value`` is an array, uses the method :py:meth:`str.index`.

   .. versionadded:: 0.5.0

.. function:: isalnum(string: str) -> bool

   Return True if all characters in ``string`` are alphanumeric using :py:meth:`str.isalnum`.

   .. versionadded:: 0.5.0

.. function:: isalpha(string: str) -> bool

   Return True if all characters in ``string`` are alphabetic using :py:meth:`str.isalpha`.

   .. versionadded:: 0.5.0

.. function:: isascii(string: str) -> bool

   Return True if all characters in ``string`` are ASCII using :py:meth:`str.isascii`.

   .. versionadded:: 0.5.0

.. function:: isdecimal(string: str) -> bool

   Return True if all characters in ``string`` are decimal using :py:meth:`str.isdecimal`.

   .. versionadded:: 0.5.0

.. function:: isdigit(string: str) -> bool

   Return True if all characters in ``string`` are digits using :py:meth:`str.isdigit`.

   .. versionadded:: 0.5.0

.. function:: isidentifier(string: str) -> bool

   Return True if all characters in ``string`` are identifiers if the string is a valid
   identifier according to the Python language definition using :py:meth:`str.isidentifier`.

   .. versionadded:: 0.5.0

.. function:: islower(string: str) -> bool

   Return True if all characters in ``string`` are lowercase using :py:meth:`str.islower`.

   .. versionadded:: 0.5.0

.. function:: isnumeric(string: str) -> bool

   Return True if all characters in ``string`` are numeric using :py:meth:`str.isnumeric`.

   .. versionadded:: 0.5.0

.. function:: isprintable(string: str) -> bool

   Return True if all characters in ``string`` are printable using :py:meth:`str.isprintable`.

   .. versionadded:: 0.5.0

.. function:: isspace(string: str) -> bool

   Return True if all characters in ``string`` are whitespace using :py:meth:`str.isspace`.

   .. versionadded:: 0.5.0

.. function:: istitle(string: str) -> bool

   Return True if all characters in ``string`` are titlecased using :py:meth:`str.istitle`.

   .. versionadded:: 0.5.0

.. function:: isupper(string: str) -> bool

   Return True if all characters in ``string`` are uppercase using :py:meth:`str.isupper`.

   .. versionadded:: 0.5.0

.. function:: lower(string: str) -> str

   Return a lowercased version of the string using :py:meth:`str.lower`.

   .. versionadded:: 0.5.0

.. function:: lstrip(string: str[, chars: str]) -> str

   Return a left-stripped version of the string using :py:meth:`str.lstrip`.

   .. versionadded:: 0.5.0

.. function:: partition(string: str, sep: str) -> list[str]

   Return an array of 3 items containing the part before the separator,
   the separator itself, and the part after the separator.

   .. versionadded:: 0.5.0

.. function:: rfind(string: str | list, sub: any[, start: int[, end: int]]) -> int

   Return the highest index in ``value`` where subvalue ``sub`` is found.
   If ``start`` and ``end`` are given, return the number of occurrences between
   ``start`` and ``end``. If not found, ``-1`` is returned. If ``value`` is a string
   it uses internally the Python's built-in function :py:meth:`str.find`
   or :py:meth:`str.index` if ``value`` is an array.

   .. versionadded:: 0.5.0

.. function:: rpartition(string: str, sep: str) -> list[str]

   Return an array of 3 items containing the part after the separator,
   the separator itself, and the part before the separator splitting the
   string at the last occurrence of ``sep``.

   .. versionadded:: 0.5.0

.. function:: rsplit(string: str[, sep: str[, maxsplit: int]]) -> list[str]

   Return a list of the words in the string, using ``sep`` as the delimiter string
   as returned from the method :py:meth:`str.rsplit`. Except for splitting from the
   right, :py:func:`rsplit` behaves like :py:func:`split`.

   .. versionadded:: 0.5.0

.. function:: split(string: str[, sep: str[, maxsplit: int]]) -> list[str]

   Return a list of the words in the string, using ``sep`` as the delimiter string
   as returned from the method :py:meth:`str.split`. If ``sep`` is not given,
   it defaults to ``None``, meaning that any whitespace string is a separator.

   .. versionadded:: 0.5.0

.. function:: splitlines(string: str[, keepends: bool]) -> list[str]

   Return a list of the lines in the string, breaking at line boundaries using
   the method :py:meth:`str.splitlines`.

   .. versionadded:: 0.5.0

.. function:: swapcase(string: str) -> str

   Return a swapped-case version of the string using :py:meth:`str.swapcase`.

   .. versionadded:: 0.5.0

.. function:: title(string: str) -> str

   Return a titlecased version of the string using :py:meth:`str.title`.

   .. versionadded:: 0.5.0

.. function:: upper(string: str) -> str

   Return an uppercased version of the string using :py:meth:`str.upper`.

   .. versionadded:: 0.5.0

.. function:: zfill(string: str, width: int) -> str

   Return a zero-padded version of the string using :py:meth:`str.zfill`.

   .. versionadded:: 0.5.0

.. function:: enumerate(string: str | list | dict) -> list[list[int, str]]

   Return an array of arrays containing the index and value of each item in the iterable.
   If the iterable is an object, the value is converted before using :py:func:`to_items`.

   .. versionadded:: 0.5.0

.. function:: to_items(string: dict) -> list[list[str, any]]

   Convert an object to an array of arrays containing the key and value of each item.

   .. versionadded:: 0.5.0

.. function:: from_items(items: list[list[str, any]]) -> dict

   Convert an array of arrays containing the key and value of each item to an object.

   .. versionadded:: 0.5.0

.. rubric:: Updater functions

The next functions take an value as the first argument, make some update
on this ``base`` object and return it updated. Useful for fix queries when
you need to return fixed contents for files.

.. function:: update(base: dict, next: dict) -> dict

   Update the ``base`` object with the ``next`` object using Python's builtin
   :py:meth:`dict.update`.

   Returns the updated ``base`` object.

   .. versionadded:: 0.7.0

.. function:: insert(base: list, index: int, item: t.Any) -> list

   Insert a ``item`` at the given ``index`` in the array ``base``.

   Returns the updated ``base`` array.

   .. versionadded:: 0.7.0

.. function:: deepmerge(base: dict, next: dict, strategy : str | list = "conservative_merger") -> dict

   Merge the ``base`` and ``next`` objects using the library :py:mod:`deepmerge`.

   Returns the updated ``base`` object.

   The argument of ``strategy`` controls how the objects are merged. It can accept
   strings with `deepmerge strategy names`_:

   .. rubric:: Example

   .. code-block:: text

      deepmerge(@, `{"foo": "bar"}`, 'always_merger')

   Or an array with 3 values, the same that takes the class :py:class:`deepmerge.merger.Merger`
   as arguments:

   * ``type_strategies``
   * ``fallback_strategies``
   * ``type_conflict_strategies``

   .. rubric:: Example

   .. code-block:: text

      deepmerge(
         @,
         `{"foo": ["bar"]}`,
         `[[["list", "append"], ["dict": "merge"]], ["override"], ["override"]]`
      )

   .. versionadded:: 0.7.0

.. function:: set(base: dict, key: str, value: t.Any) -> dict

   Set the value of the ``key`` in the ``base`` object to ``value``.

   Returns the updated ``base`` object.

   .. versionadded:: 0.7.0

.. function:: unset(base: dict, key: str) -> dict

   If has it, remove the ``key`` from the ``base`` object.

   Returns the updated ``base`` object.

   .. versionadded:: 0.7.0

.. function:: replace(base: str, old: str, new: str[, count: int | None = None])

   Replace the ``old`` string with the ``new`` string in the ``base`` string
   using the Python's built-in string method :py:meth:`str.replace`.

   Returns the updated ``base`` string.

   .. versionadded:: 0.7.0

.. function:: removeprefix(string: str, prefix: str) -> str

   Return a string with the given prefix removed using :py:meth:`str.removeprefix`.

   .. versionadded:: 0.5.0

.. function:: removesuffix(string: str, suffix: str) -> str

   Return a string with the given suffix removed using :py:meth:`str.removesuffix`.

   .. versionadded:: 0.5.0

.. function:: format(schema: str, *args: any) -> str

   Return a string formatted using the Python's built-in :py:func:`format` function.
   The variable ``schema`` only accepts numeric indexes delimited by braces ``{}``
   for positional arguments in ``*args``.

   .. versionadded:: 0.5.0

.. function:: strip(string: str[, chars: str]) -> str

   Return a stripped version of the string using :py:meth:`str.strip`.

   .. versionadded:: 0.5.0

.. function:: rstrip(string: str[, chars: str]) -> str

   Return a right-stripped version of the string using :py:meth:`str.rstrip`.

   .. versionadded:: 0.5.0

.. function:: capitalize(string: str) -> str

   Capitalize the first letter of a string using :py:meth:`str.capitalize`.

   .. versionadded:: 0.5.0

.. function:: casefold(string: str) -> str

   Return a casefolded copy of a string using :py:meth:`str.casefold`.

   .. versionadded:: 0.5.0

.. function:: center(string: str, width: int[, fillchar: str]) -> str

   Return centered in a string of length ``width`` using :py:meth:`str.center`.

   .. versionadded:: 0.5.0

.. function:: ljust(string: str, width: int[, fillchar: str]) -> str

   Return a left-justified version of the string using :py:meth:`str.ljust`.

   .. versionadded:: 0.5.0

.. function:: rjust(string: str, width: int[, fillchar: str]) -> str

   Return a right-justified version of the string using :py:meth:`str.rjust`.

   .. versionadded:: 0.5.0

.. _JMES paths: https://jmespath.org
.. _JMESPath builtin functions: https://jmespath.org/specification.html#built-in-functions
.. _deepmerge strategy names: https://deepmerge.readthedocs.io/en/latest/strategies.html#builtin-strategies
.. _sys.platform: https://docs.python.org/3/library/sys.html#sys.platform

.. rubric:: Github functions

The functions which name starts with `gh_` are functions that connect to
only Github sources.

.. function:: gh_tags(repo_owner: str, repo_name: str[, only_semver: bool = False]) -> list[str]

   Return the list of tags of the Github repository, ordered from latest to oldest.

   If you pass the third parameter as a ``true`` value, only the tags that
   are following semantic versioning (even if they are prepended with some
   text like ``v``) will be returned.

   This function is really useful setting the ``rev`` properties in
   `.pre-commit-config.yaml` files.

   .. versionadded:: 0.7.1

.. rubric:: Fix queries

The verbs of the jmespath plugin can fix files by applying a JMESPath
query over the previous content of the files. The fix-queries arguments
are always optional.

If no fix-query is provided, **project-config** will attempt to build an expected
node tree instance to update the content parsing the other queries arguments
and the expected value.

The query will be a syntax like (example merging objects):

.. code-block:: text

   deepmerge(@, `{ "foo": "bar" }`)

Where ``@`` is the previous content of the file.

The result from this JMESPath expression will be the next content of the file.
So these transformer functions like :py:func:`deepmerge`, :py:func:`insert` or
:py:func:`update` allow you to edit your files with total flexibility.

.. rubric:: Automatic fixes

Queries that are simple can be automatically fixed by the plugin. For example,
a constant query with their expected value:

.. tabs::

   .. tab:: package.json (before)

      .. code-block:: json

         {
            "name": "my-project"
         }

   .. tab:: package.json (after)

      .. code-block:: json

         {
            "name": "my-project",
            "license": "BSD-3-Clause"
         }

   .. tab:: style.json5 (rule)

      .. code-block:: js

         {
           files: ["package.json"],
           JMESPathsMatch: [["license", "BSD-3-Clause"]]
         }

Currently, is possible to automatically fix the following cases:

* Query to constant.
* Query to constant in nested objects.
* Expression using the ``type`` function like ``type(foo.bar)`` with expected value as ``'array'`` (creates ``{foo: {bar: []}}`` nodes if doesn't exists before).
* Indexed expressions with indexes like ``type(foo[0].bar)`` with expected value as ``'object'`` (prepends, ``{bar: {}}`` to the array ``bar``, creating it if does not exists).
* Forbidden key in root object like ``contains(keys(@), 'foo')`` with expected value as ``false`` (removes the key ``foo`` from the root object).

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

.. versionchanged:: 0.7.0

   The verb also accepts fix queries as third item of rows.

crossJMESPathsMatch
===================

JMESPaths matching between multiple files.

Accepts an array of arrays. Each one of these arrays must have the syntax:

.. code-block:: js

   [
     "filesJMESPathExpression",  // expression to query each file in `files` property of the rule
     ["otherFile.ext", "JMESPathExpression"]...,  // optionally other files
     "finalJMESPathExpression",  // an array with results of previous expressions as input
     expectedValue,  // value to compare with the result of final JMESPath expression
   ]

The executed steps are:

1. For each object-serialized file in ``files`` property of the rule.
2. Execute ``"filesJMESPathExpression"`` and append the result to a temporal array.
3. For each pair of ``["otherFile.ext", "JMESPathExpression"]``, execute
   ``"JMESPathExpression"`` against the object-serialized version of
   ``"otherFile.ext"`` and append each result to the temporal array.
4. Execute ``"finalJMESPathExpression"`` against the temporal array.
5. Compare the final result with ``expectedValue`` and raise error if not match.

.. tip::

   Other file paths can be URLs if you want to match against online sources.

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
           [
             "tool.poetry.metadata",
             ["docs/conf.py", "release"],
             "op([0], '==', [1])",
             true,
           ],
         ],
         hint: "Versions of documentation and metadata must be the same"
       }
     ]
   }

Note that you can pass whatever number of other files, even 0 and just apply
``files`` and ``final`` expressions to each file in ``files`` property of
the rule. For example, the next configuration would not raise errors:

.. tabs::

   .. tab:: style.json5

      .. code-block:: js

         {
           rules: [
             {
               files: ["foo.json"],
               crossJMESPathsMatch: [
                 ["bar", "[0].baz", 7],
               ]
             }
           ]
         }

   .. tab:: foo.json

      .. code-block:: json

         {"bar": {"baz": 7}}

You can also override the :doc:`../in-depth/serialization` to use for opening
other files using ``file/path.ext?serializer`` syntax. For example, to open a
Python file line by line:

.. tabs::

   .. tab:: file.py

      .. code-block:: py

         foo = True
         bar = False

   .. tab:: style.json5

      .. code-block:: js

         {
           rules: [
             {
               files: ["file.py"],  // just asserts that the file exists
               crossJMESPathsMatch: [
                 ["null", ["file.py?text", "[0]"], "[1]", "foo = True"],
               ]
             }
           ]
         }

.. seealso::

   * :doc:`../in-depth/serialization`
   * :ref:`Example of crossJMESPath against online source<examples:JMESPath against online sources>`
   * :ref:`Example comparing values between files<examples:Compare values between files>`
   * :ref:`Example checking lines sorting<examples:TOML sections order>`

.. versionadded:: 0.4.0

ifJMESPathsMatch
================

Compares a set of JMESPath expressions against results.

JSON-serializes each file in the ``ifJMESPathsMatch`` property
of the rule and executes each expression given in the first item of the
tuples passed as value for each file. If a result don't match,
skips the rule.

.. rubric:: Example

If ``inline-quotes`` config of `flake8`_ is defined to use double quotes,
`black`_ must be configured as the formatting tool in ``pyproject.toml``:

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

.. _flake8: https://flake8.pycqa.org
.. _black: https://black.readthedocs.io
