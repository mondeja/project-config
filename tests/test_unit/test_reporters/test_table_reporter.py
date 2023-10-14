import pytest
from project_config.reporters import table


@pytest.mark.parametrize(
    ("errors", "expected_result"),
    (
        pytest.param(
            [],
            """files    message    definition    hint
-------  ---------  ------------  ------""",
            id="ok",
        ),
        pytest.param(
            [
                {
                    "file": "foo.py",
                    "message": "message",
                    "definition": "definition",
                },
            ],
            """files    message    definition    hint
-------  ---------  ------------  ------
foo.py   message    definition""",
            id="basic",
        ),
        pytest.param(
            [
                {
                    "file": "foo.py",
                    "message": "message 1",
                    "definition": "definition 1",
                },
                {
                    "file": "foo.py",
                    "message": "message 2",
                    "definition": "definition 2",
                    "hint": "a hint to solve it",
                },
                {
                    "file": "bar.py",
                    "message": "message 3",
                    "definition": "definition 3",
                },
            ],
            """files    message    definition    hint
-------  ---------  ------------  ------------------
foo.py   message 1  definition 1
         message 2  definition 2  a hint to solve it
bar.py   message 3  definition 3""",
            id="complex",
        ),
    ),
)
def test_errors_report(errors, expected_result, assert_errors_report):
    assert_errors_report(table, errors, expected_result, fmt="simple")
