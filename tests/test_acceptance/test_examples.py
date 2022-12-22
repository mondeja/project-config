import os
import shutil
import sys

import pytest
from testing_helpers import mark_end2end, rootdir

from project_config.__main__ import run
from project_config.commands.check import check
from project_config.exceptions import ProjectConfigException


def _parse_example_metadata(example_dir):
    readme_rst_filepath = os.path.join(example_dir, "README.rst")
    with open(readme_rst_filepath, encoding="utf-8") as f:
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
                if key == "fixable":
                    metadata[key] = value.lower() == "true"
                else:
                    metadata[key] = value.replace("\\n", "\n")
            else:
                _inside_metadata = False
    return metadata


def _collect_examples(online=False):
    examples = []
    examples_dir = os.path.join(rootdir, "examples")
    for example_dirname in sorted(os.listdir(examples_dir)):
        if (
            not example_dirname.startswith("_")
            and not example_dirname[0].isdigit()
        ):
            continue
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
                example_metadata.get("fixable", True),
                id=example_dirname,
            ),
        )
    return examples


def _run_example(
    example_dir,
    expected_exitcode,
    expected_stderr,
    fixable,
    interface,
    capsys,
    tmp_path,
    fake_cli_namespace,
):
    if interface == "CLI":
        exitcode = run(["--nocolor", "--rootdir", example_dir, "check"])
        out, err = capsys.readouterr()
        assert exitcode == expected_exitcode, err
        assert err == expected_stderr
        assert out == ""

        temp_example_dir = shutil.copytree(
            example_dir,
            tmp_path / os.path.basename(example_dir),
        )

        if exitcode == 0:
            exitcode = run(["--nocolor", "--rootdir", temp_example_dir, "fix"])
            out, err = capsys.readouterr()
            assert exitcode == 0, err
            assert err == ""
            assert out == ""
        elif fixable:
            exitcode = run(["--nocolor", "--rootdir", temp_example_dir, "fix"])
            out, err = capsys.readouterr()
            msg = f"{out}\n---\n{err}"
            assert out == "", msg
            assert "(FIXED)" in err, msg
            assert exitcode == 1, msg

            exitcode = run(["--nocolor", "--rootdir", temp_example_dir, "fix"])
            out, err = capsys.readouterr()
            msg = f"{out}\n---\n{err}"
            assert out == "", msg
            assert err == "", msg
            assert exitcode == 0, msg

    else:
        namespace = fake_cli_namespace(rootdir=example_dir, color=False)
        if expected_stderr:
            with pytest.raises(ProjectConfigException) as exc:
                check(namespace)
            assert str(exc.value) == expected_stderr.rstrip("\n")
        else:
            check(namespace)


@pytest.mark.parametrize("interface", ("CLI", "API"))
@pytest.mark.parametrize(
    ("example_dir", "expected_exitcode", "expected_stderr", "fixable"),
    _collect_examples(),
)
def test_examples(
    example_dir,
    expected_exitcode,
    expected_stderr,
    fixable,
    interface,
    chdir,
    capsys,
    tmp_path,
    fake_cli_namespace,
):
    if os.path.basename(example_dir).startswith(
        "_005-conditional-files-existence-fails",
    ):
        if "win" in sys.platform:
            pytest.skip("This example is not supported on Windows")
    _run_example(
        example_dir,
        expected_exitcode,
        expected_stderr,
        fixable,
        interface,
        chdir,
        capsys,
        tmp_path,
        fake_cli_namespace,
    )


@mark_end2end
@pytest.mark.parametrize("interface", ("CLI", "API"))
@pytest.mark.parametrize(
    ("example_dir", "expected_exitcode", "expected_stderr", "fixable"),
    _collect_examples(online=True),
)
def test_examples_with_online_sources_check(
    example_dir,
    expected_exitcode,
    expected_stderr,
    fixable,
    interface,
    chdir,
    capsys,
    tmp_path,
    fake_cli_namespace,
):
    _run_example(
        example_dir,
        expected_exitcode,
        expected_stderr,
        fixable,
        interface,
        chdir,
        capsys,
        tmp_path,
        fake_cli_namespace,
    )
