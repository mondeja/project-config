import os

import pytest
from project_config.serializers.python import dumps, loads


@pytest.mark.parametrize(
    ("string", "kwargs", "expected_result"),
    (
        pytest.param(
            "foo = 'bar'\nbaz = 1",
            {},
            {"foo": "bar", "baz": 1},
            id="basic",
        ),
        pytest.param(
            'raise Exception("foo")',
            {},
            Exception,
            id="exception",
        ),
        pytest.param(
            "foo = 1\nbar = 2\nbaz = bool",
            {},
            {"foo": 1, "bar": 2, "baz": bool},
            id="py-object",
        ),
        pytest.param(
            "foo = 1\nbar = 2\nbaz = bool",
            {"namespace": {"__file__": os.path.basename(__file__)}},
            {
                "foo": 1,
                "bar": 2,
                "baz": bool,
                "__file__": os.path.basename(__file__),
            },
            id="previous-namespace",
        ),
    ),
)
def test_python_loads(string, kwargs, expected_result, maybe_raises):
    with maybe_raises(expected_result):
        assert loads(string, **kwargs) == expected_result


@pytest.mark.parametrize(
    ("obj", "expected_result"),
    (
        pytest.param(
            {"foo": "bar", "baz": 1},
            'foo = "bar"\nbaz = 1\n',
            id="basic",
        ),
        pytest.param(
            {"foo": 1, "bar": 2, "baz": bool, "qux": "a string"},
            'foo = 1\nbar = 2\nbaz = bool\nqux = "a string"\n',
            id="type",
        ),
        pytest.param(
            {"foo": 1, "bar": {"baz": bool, "qux": "a string"}},
            'foo = 1\nbar = {"baz": bool, "qux": "a string"}\n',
            id="dict",
        ),
        pytest.param(
            {
                "baz": [1, 2, 3, 4, 5, bool, True, "string"],
                "bar": [
                    1,
                    2.321,
                    True,
                    None,
                    False,
                    str,
                    "foo",
                    "bar",
                    "baz",
                    "qux",
                ],
                "foo": {
                    "bar": bool,
                    "baz": "a string",
                    "bbar": True,
                    "bbaz": False,
                    "nfoo": None,
                },
            },
            """baz = [1, 2, 3, 4, 5, bool, True, "string"]
bar = [
    1,
    2.321,
    True,
    None,
    False,
    str,
    "foo",
    "bar",
    "baz",
    "qux",
]
foo = {
    "bar": bool,
    "baz": "a string",
    "bbar": True,
    "bbaz": False,
    "nfoo": None,
}
""",
            id="list",
        ),
    ),
)
def test_python_dumps(obj, expected_result):
    assert dumps(obj) == expected_result
