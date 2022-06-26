import contextlib
import io
import os

import pytest
from testing_helpers import rootdir

from project_config.__main__ import run
from project_config.exceptions import ProjectConfigException
from project_config.project import Project


def _parse_example_metadata(example_dir):
    readme_rst_filepath = os.path.join(example_dir, "README.rst")
    with open(readme_rst_filepath) as f:
        readme_lines = f.read().splitlines()

    metadata = {}
    _inside_metadata = False
    for line in readme_lines:
        if not _inside_metadata:
            if line == "..":
                _inside_metadata = True
        else:
            if line.startswith("   "):
                key = line.lstrip().split(":")[0].lower()
                value = line.split(":", maxsplit=1)[-1].strip()
                metadata[key] = value.replace("\\n", "\n")
            else:
                _inside_metadata = False
    return metadata


def _collect_examples():
    examples = []
    examples_dir = os.path.join(rootdir, "examples")
    for example_dirname in sorted(os.listdir(examples_dir)):
        example_dirpath = os.path.join(examples_dir, example_dirname)
        example_metadata = _parse_example_metadata(example_dirpath)
        expected_stderr = example_metadata.get("stderr", "")
        if expected_stderr:
            expected_stderr += "\n"
        examples.append(
            pytest.param(
                example_dirpath,
                int(example_metadata.get("exitcode", 0)),
                expected_stderr,
                id=example_dirname,
            ),
        )
    return examples


@pytest.mark.parametrize("interface", ("CLI", "API"))
@pytest.mark.parametrize(
    ("example_dir", "expected_exitcode", "expected_stderr"),
    _collect_examples(),
)
def test_examples_check(
    example_dir,
    expected_exitcode,
    expected_stderr,
    interface,
    chdir,
):
    args = ["--nocolor", "check"]

    # from command line
    if interface == "CLI":
        stderr_stream = io.StringIO()
        with chdir(example_dir), contextlib.redirect_stderr(stderr_stream):
            exitcode = run(args)
            stderr = stderr_stream.getvalue()
            assert exitcode == expected_exitcode, stderr
            assert stderr == expected_stderr
    else:
        # from API
        with chdir(example_dir):
            project = Project(None, example_dir, "default", False)
            if expected_stderr:
                with pytest.raises(ProjectConfigException) as exc:
                    project.check(args)
                assert str(exc.value) == expected_stderr.rstrip("\n")
            else:
                project.check(args)
