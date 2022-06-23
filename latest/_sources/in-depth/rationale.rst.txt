#########
Rationale
#########

This project has been created to help me to made a transition from
setuptools/pip based Python development workflow to a more modern
Poetry based one. I wanted to be able to parse conveniently all
configuration files to check certain common patterns or the migration
would be impossible.

Nowadays, configuring properly a project in any almost language with
all the tools needed for code quality assurance and documentation
is a real pain.

Taking Python as example, you need to configure for a project:

* Black: line length and target lowest Python version.
* Isort: line length remembering that is one lower than Black, target lowest Python version, extra standard library modules depending on lowest Python version, all the sections and the formatting. Some things like section and formatting usually are the same in all of the projects of a maintainer.
* Flake8: line length, inline quotes (use double we are using Black, remember) plus all the standard that the maintainer follow.
* pre-commit: of course, how these tools will be executed? You need all the pre-commit hooks, copy and paste over and over... eventually asking yourself trascendental questions like: is this tool using revisions starting with `v` or not?
* For typing guys, Mypy: the target lowest Python version.

And this is only the beggining, I personally use a lot of other tools with
pre-commit. Just think about increasing the lowest version number targetted,
is a complete nightmare!

With **project-config** I've a style which track these lowest Python version
values in all files, so after updating the style file I run ``check`` and
**project-config** shows me all the changes needed.

************
Alternatives
************

Looking for a tool to solve this problem I found `nitpick`_, which is
essentially designed with the same goals than **project-config**
in mind but different approach, which I don't really like. Don't blame me,
`I've created the styles previously <https://github.com/mondeja/nitpick-styles>`_
with `nitpick`_, but I couldn't create some assertions because of the
serious limitations in his design.

So I've created **project-config** inspired by `nitpick`_. In fact, the
configuration follows the same pattern, but the plugin system and the concept
of :doc:`./serialization` is quite different. The main differences are:

* `nitpick`_ enforces the definition configuration values as constants using TOML files, but **project-config** just make assertions executing certain rules. This approach allows to check more things but turns the implementation of a ``fix`` command more difficult, though not impossible.
* `nitpick`_ has a serious limitation about how to query object structures, which has given rise to the monstrosity of `Special configurations <https://nitpick.readthedocs.io/en/latest/styles.html?highlight=pre-commit#special-configurations>`_, while **project-config** deals with this problem using `JMESPath`_.

.. _nitpick: https://nitpick.readthedocs.io/en/latest/
.. _JMESPath: https://jmespath.org/
