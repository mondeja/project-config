import os
import typing as t

from project_config.plugins.types import Files, Rule, VerbResult


class IncluderPlugin:
    @classmethod
    def verb_includeAllLines(
        cls,
        value: t.List[str],
        files: Files,
        rule: Rule,
        rule_index: int,
    ) -> VerbResult:
        expected_lines = [line.strip("\r\n") for line in value]
        result: VerbResult = {"errors": []}

        for f, (fpath, fcontent) in enumerate(files):
            if not isinstance(fcontent, str):  # is directory
                result["errors"].append(
                    {
                        "message": (
                            f"Found directory defined at 'rules[{rule_index}].files[{f}]'."
                            " The verb 'includeAllLines' does not accepts directories as"
                            " inputs."
                        ),
                        "file": fpath + os.sep,
                    }
                )
                continue

            # Normalize newlines
            fcontent_lines = fcontent.replace("\r\n", "\n").split("\n")
            for l, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    result["errors"].append(
                        {
                            "message": (
                                f"Expected line '{expected_line}' defined"
                                f" at 'rules[{rule_index}].includeAllLines[{l}]'"
                                f" not found"
                            ),
                            "file": fpath,
                        }
                    )

        return result
