import os
import typing as t

from project_config import Files, Results, Rule


class IncludePlugin:
    @classmethod
    def includeAllLines(
        cls,
        value: t.List[str],
        files: Files,
        rule: Rule,
    ) -> Results:
        expected_lines = [line.strip("\r\n") for line in value]

        for f, (fpath, fcontent) in enumerate(files):
            if fcontent is None:
                continue
            elif not isinstance(fcontent, str):
                yield "error", {
                    "message": (
                        f"Directory found but he verb 'includeAllLines' does not"
                        " accepts directories as inputs"
                    ),
                    "file": fpath.rstrip(os.sep) + os.sep,
                    "definition": f".files[{f}]",
                }
                continue

            # Normalize newlines
            fcontent_lines = fcontent.replace("\r\n", "\n").split("\n")
            for l, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    yield "error", {
                        "message": f"Expected line '{expected_line}' not found",
                        "file": fpath,
                        "definition": f".includeAllLines[{l}]",
                    }

    @classmethod
    def ifIncludeAllLines(
        cls,
        value: t.List[str],
        files: Files,
        rule: Rule,
    ) -> Results:
        pass
