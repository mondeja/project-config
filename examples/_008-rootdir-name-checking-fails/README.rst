..
   Name: Assert root directory name
   Exitcode: 1
   Stderr: .project-config.toml\n  - JMESPath 'regex_match('[a-z0-9-]+$', rootdir_name())' does not match. Expected True, returned False rules[0].JMESPathsMatch[0]

Check that the name of the directory that is the root of the project
matches against certain regular expression.
