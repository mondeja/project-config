..
   Name: Conditionals files existence (fails rule 1)
   Exitcode: 1
   Stderr: foobarbaz.toml\n  - (FIXABLE) Expected existing file does not exists rules[0].files[0]

* 1st rule: if the directory `src/` exists, the file `foobarbaz.toml` must exists too.
* 2nd rule: if the file `pyproject.toml` exists, a Python file must be present in the root directory.
