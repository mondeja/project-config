#######
Styling
#######

Styles can be defined in any object-serializable file format (see
:ref:`in-depth/serialization:Objects serialization`).

We recommend to use YAML or JSON5 because are the most readable, flexible
and allows comments, which are really useful writing styles.

Each style must be an object with the following keys:

* ``rules`` (optional if ``extends`` is specified)
* ``extends`` (optional if ``rules`` is specified)
* ``plugins`` (optional)

At least one rule or extension is required to be a valid style. At least one
rule must be collected after styles extensions to be a valid merged style.

**********************
``rules`` (`object[]`)
**********************

Define the actions to execute against files. It must be an array of objects
with at least one object.

``files`` (`string[]` or `object{not{} | not[]}`)
=================================================

Unique mandatory field for all rules. It specifies the subject of the rule,
that is, the files for which the verbs will be applied.

It must be either an array of strings or an object with an unique key ``not``.----

Defining ``files`` as an array of strings enforce the existence of these files.
If they don't exist, no actions will be executed. The existence of these files
is mandatory for execute the rest of actions of the rule.

Enforce files absence
---------------------

Defining ``files`` as an object, it must be an unique key ``not``. The value
of ``not`` must be either:

* An object whose keys are the files that must not exist and a message for each value indicating a reason that explain why this file must be absent.
* An array of strings with the paths to the files that must not exist.

When enforcing absence of files no other actions can be defined in the rule,
as this has no sense. The attempt will raise an error validating the style.

File syntax convention
----------------------

* Files are defined relative to the root directory of the project, which will be the current working directory if no other is passed in `--rootdir` CLI argument.
* Paths terminated with ``/`` will be treated as directories using the Unix separator, even in Windows systems.

************************
``extends`` (`string[]`)
************************

Array of strings to define other styles from which the current will extend.
Extended rules will be executed before the rules of the current style.

Can be defined with the same syntax of styles in configuration, from a local
file, a URI resource... Resources fetched can be defined with relative URIs
to their fetchers locations. So giving a style located at
``gh://author/project/path/to/file.json5`` we can reference with
``extends`` to a resource located at ``gh://author/project/path/other/file.json5``
using ``extends: ["../other/file.json5"]`` inside the style
``gh://author/project/path/to/file.json5``.

************************
``plugins`` (`string[]`)
************************

Additional third party plugin names on which the rules of the style depend.
Built-in plugins don't need to be defined here, as are loaded by default.
