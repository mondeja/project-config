..
   Name: TOML sections order
   Exitcode: 1
   Stderr: pyproject.toml\n  - JMESPath 'op(op([1], 'indexOf', '[foo]'), '<', op([1], 'indexOf', '[bar]'))' does not match. Expected True, returned False rules[0].crossJMESPathsMatch[0] The section '[foo]' must be defined before the section '[bar]'

Check that the section ``[foo]`` of a TOML file is placed before the section ``[bar]``.
