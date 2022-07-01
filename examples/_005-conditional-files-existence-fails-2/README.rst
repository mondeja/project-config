..
   Name: Conditionals files existence (fails rule 2)
   Exitcode: 1
   Stderr: *.py\n  - Expected existing file does not exists rules[1].files[0]

* 1st rule: if the directory `src/` exists, the file `pyproject.toml` must exists too.
* 2nd rule: if the file `pyproject.toml` exists, a Python file must be present in the root directory.
