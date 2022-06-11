import os
import typing as t

from project_config import (
    Error,
    InterruptingError,
    Results,
    ResultValue,
    Rule,
    Tree,
)
from project_config.utils import normalize_newlines


def _directories_not_accepted_as_inputs_error(
    action_type: str,
    action_name: str,
    dir_path: str,
    definition: str,
) -> t.Dict[str, str]:
    return {
        "message": (
            f"Directory found but the {action_type} '{action_name}' does not"
            " accepts directories as inputs"
        ),
        "file": f"{dir_path.rstrip(os.sep)}/",
        "definition": definition,
    }


class IncludePlugin:
    @classmethod
    def includeAllLines(
        cls,
        value: t.List[str],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        expected_lines = [line.strip("\r\n") for line in value]

        for f, (fpath, fcontent) in enumerate(tree.files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield InterruptingError, _directories_not_accepted_as_inputs_error(
                    "verb",
                    "includeAllLines",
                    fpath,
                    f".files[{f}]",
                )
                continue

            # Normalize newlines
            fcontent_lines = normalize_newlines(fcontent).split("\n")
            for l, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    yield Error, {
                        "message": f"Expected line '{expected_line}' not found",
                        "file": fpath,
                        "definition": f".includeAllLines[{l}]",
                    }

    @classmethod
    def ifIncludeAllLines(
        cls,
        value: t.Dict[str, t.List[str]],
        tree: Tree,
        rule: Rule,
    ) -> Results:
        for fpath, expected_lines in value.items():
            fcontent = tree.get_file_content(fpath)

            if fcontent is None:
                yield InterruptingError, {
                    "message": "File specified in conditional 'ifIncludeAllLines' not found",
                    "file": fpath,
                    "definition": f"ifIncludeAllLines[{fpath}]",
                }
                return
            elif not isinstance(fcontent, str):
                yield InterruptingError, _directories_not_accepted_as_inputs_error(
                    "conditional",
                    "ifIncludeAllLines",
                    fpath,
                    f"ifIncludeAllLines[{fpath}]",
                )
                return

            expected_lines = [line.strip("\r\n") for line in expected_lines]
            fcontent_lines = normalize_newlines(fcontent).split("\n")
            for expected_line in expected_lines:
                if expected_line not in fcontent_lines:
                    yield ResultValue, False
                    return
        yield ResultValue, True

    # TODO: add jsonschema for plugin action values
