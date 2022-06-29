..
   Name: Conditionals
   Exitcode: 1
   Stderr: docs/\n  - Directory found but the conditional 'ifIncludeLines' does not accepts directories as inputs rules[0].ifIncludeLines[docs/]

If `docs/` folder includes the line ``__pycache__/`` a `pyproject.toml`
file must be present. Using ``ifIncludeLines`` conditional raises
an interrupt error because it does not accept directories as inputs.
