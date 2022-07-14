..
   Name: Replacing code blocks languages in RST documents
   Exitcode: 1
   Stderr: file.rst\n  - (FIXABLE) Found expected content to exclude '.. code-block::  ' rules[0].excludeContent[0]\n  - (FIXABLE) Found expected content to exclude '.. code-block:: bash' rules[0].excludeContent[1]\n  - (FIXABLE) Found expected content to exclude '.. code-block:: json5' rules[0].excludeContent[2]

Don't allow code blocks in RST documentation files:

* Bash is not a POSIX compliant shell, use Shell lexer.
* Pygments' JSON5 lexer is not implemented yet, use Javascript lexer.
