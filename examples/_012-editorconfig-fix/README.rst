..
   Name: Autofixing .editorconfig
   Exitcode: 1
   Stderr: .editorconfig\n  - (FIXABLE) JMESPath 'type("")' does not match. Expected 'object', returned 'null' rules[0].JMESPathsMatch[1]\n  - (FIXABLE) JMESPath '"".root' does not match. Expected True, returned None rules[0].JMESPathsMatch[2]\n  - (FIXABLE) JMESPath '"*".end_of_line' does not match. Expected 'lf', returned None rules[0].JMESPathsMatch[3]\n  - (FIXABLE) JMESPath '"*".indent_style' does not match. Expected 'space', returned None rules[0].JMESPathsMatch[4]\n  - (FIXABLE) JMESPath '"*".charset' does not match. Expected 'utf-8', returned None rules[0].JMESPathsMatch[5]\n  - (FIXABLE) JMESPath '"*".trim_trailing_whitespace' does not match. Expected True, returned None rules[0].JMESPathsMatch[6]

If you run the next example using ``project-config fix`` subcommand
without creating an `.editorconfig` file it will be created and populated
with the sections defined in the rule.
