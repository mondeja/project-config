import types
import typing as t


VerbResult = t.Dict[str, t.List[str]]


class IncluderPlugin:
    def verb_includeAllLines(
        self, value: t.List[str], rule: t.Any, rule_index: int
    ) -> VerbResult:
        expected_lines = [line.strip("\r\n") for line in value]
        result: VerbResult = {
            "errors": [],
            "fixes": [],
        }

        for f, fpath, fcontent in enumerate(rule["files"]):
            if isinstance(fcontent, types.GeneratorType):  # is directory
                result["errors"].append(
                    f"Found directory defined at rules[{rule_index}].files[{f}]."
                    " The verb 'includeAllLines' can't accept directories as inputs."
                )
                continue

            # Normalize newlines
            fcontent_lines = fcontent.replace("\r\n", "\n").split("\n")
            for l, expected_line in enumerate(expected_lines):
                if expected_line not in fcontent_lines:
                    result["errors"].append(
                        f"Expected line '{expected_line}' defined"
                        f" at 'rules[{rule_index}].includeAllLines[{l}]'"
                        f" not found in file {fpath}"
                    )

        return result
