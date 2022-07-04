import os

import pytest
from testing_helpers import mark_end2end, rootdir

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


def _collect_examples(online=False):
    examples = []
    examples_dir = os.path.join(rootdir, "examples")
    for example_dirname in sorted(os.listdir(examples_dir)):
        example_dirpath = os.path.join(examples_dir, example_dirname)
        example_metadata = _parse_example_metadata(example_dirpath)
        expected_stderr = example_metadata.get("stderr", "")
        if expected_stderr:
            expected_stderr += "\n"
        if not online and example_metadata.get("online", "false") == "true":
            continue
        elif online and example_metadata.get("online", "false") == "false":
            continue
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
    capsys,
):
    args = ["--nocolor", "check"]

    if interface == "CLI":
        with chdir(example_dir):
            exitcode = run(args)
            out, err = capsys.readouterr()
            assert exitcode == expected_exitcode, err
            assert err == expected_stderr
            assert out == ""
    else:
        with chdir(example_dir):
            project = Project(None, example_dir, {"name": "default"}, False)
            if expected_stderr:
                with pytest.raises(ProjectConfigException) as exc:
                    project.check(args)
                assert str(exc.value) == expected_stderr.rstrip("\n")
            else:
                project.check(args)


@mark_end2end
@pytest.mark.parametrize("interface", ("CLI", "API"))
@pytest.mark.parametrize(
    ("example_dir", "expected_exitcode", "expected_stderr"),
    _collect_examples(online=True),
)
def test_examples_with_online_sources_check(
    example_dir,
    expected_exitcode,
    expected_stderr,
    interface,
    chdir,
    capsys,
):
    args = ["--nocolor", "check"]

    if interface == "CLI":
        with chdir(example_dir):
            exitcode = run(args)
            out, err = capsys.readouterr()
            assert exitcode == expected_exitcode, err
            assert err == expected_stderr
            assert out == ""
    else:
        with chdir(example_dir):
            project = Project(None, example_dir, {"name": "default"}, False)
            if expected_stderr:
                with pytest.raises(ProjectConfigException) as exc:
                    project.check(args)
                assert str(exc.value) == expected_stderr.rstrip("\n")
            else:
                project.check(args)
