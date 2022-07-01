..
   Name: Compare values between serializable files
   Exitcode: 1
   Stderr: pyproject.toml\n  - JMESPath 'tool.poetry.version' does not match. Expected '1.0.0', returned '1.0.1' rules[0].crossJMESPathsMatch[0]

The version defined in ``__version__`` inside a Python script must match
the metadata defined in `pyproject.toml` file.
