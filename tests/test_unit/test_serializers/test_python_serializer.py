import os

import pytest

from project_config.serializers.python import loads


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
def test_python_serializer(string, kwargs, expected_result, maybe_raises):
    with maybe_raises(expected_result):
        assert loads(string, **kwargs) == expected_result
