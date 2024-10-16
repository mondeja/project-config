import os

from testing_helpers import rootdir


CI_REFERENCE_FILEPATH = os.path.join(
    rootdir,
    "docs",
    "reference",
    "ci.rst",
)

PYPROJECT_TOML_FILEPATH = os.path.join(rootdir, "pyproject.toml")


def test_ci_reference_github_actions_python_version():
    expected_python_version = None
    with open(PYPROJECT_TOML_FILEPATH, encoding="utf-8") as f:
        lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if line == "[tool.hatch.envs.default]":
                expected_python_version = lines[i + 1].split('"')[1]
                break

    with open(CI_REFERENCE_FILEPATH, encoding="utf-8") as f:
        assert f'python-version: "{expected_python_version}"' in f.read(), (
            "The python version in the CI reference file"
            f" ({os.path.relpath(CI_REFERENCE_FILEPATH, rootdir)}) does not"
            " match the python version in pyproject.toml"
            f" ({expected_python_version})."
            " Please update the CI reference file."
        )
