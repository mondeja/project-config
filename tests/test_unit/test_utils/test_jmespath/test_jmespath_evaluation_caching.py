"""Assert that the jmespath evaluation cache works as expected."""

import os

import pytest

from project_config.utils import jmespath as jmespath_utils


ROOTDIR_NAME = os.path.basename(os.getcwd())


@pytest.mark.parametrize(
    ("expression", "instance", "expected_result"),
    (
        pytest.param("rootdir_name()", {}, ROOTDIR_NAME, id="rootdir_name"),
        pytest.param(
            "rootdir",
            {"rootdir": "foobarbaz"},
            "foobarbaz",
            id="rootdir",
        ),
        pytest.param(
            "getenv('PROJECT_CONFIG')",
            "{}",
            "true",
            id="getenv(...)",
        ),
        pytest.param(
            "gh_tags",
            {},
            None,
            id="gh_tags",
        ),
        pytest.param(
            "listdir",
            {"listdir": "bar"},
            "bar",
            id="listdir",
        ),
        pytest.param(
            "isfile",
            {"isfile": "bar"},
            "bar",
            id="isfile",
        ),
        pytest.param(
            "isdir",
            {"isdir": "bar"},
            "bar",
            id="isdir",
        ),
        pytest.param(
            "exists",
            {"exists": "bar"},
            "bar",
            id="exists",
        ),
        pytest.param(
            "dirname",
            {"dirname": "bar"},
            "bar",
            id="dirname",
        ),
        pytest.param(
            "basename",
            {"basename": "bar"},
            "bar",
            id="basename",
        ),
        pytest.param(
            "extname",
            {"extname": "bar"},
            "bar",
            id="extname",
        ),
        pytest.param(
            "mkdir",
            {"mkdir": "bar"},
            "bar",
            id="mkdir",
        ),
        pytest.param(
            "rmdir",
            {"rmdir": "bar"},
            "bar",
            id="rmdir",
        ),
        pytest.param(
            "glob",
            {"glob": "bar"},
            "bar",
            id="glob",
        ),
    ),
)
def test_excluded_expressions_from_caching_are_not_cached(
    expression,
    instance,
    expected_result,
    mocker,
    monkeypatch,
):
    """Assert that excluded expressions are not cached."""
    # set environment variables used by tests
    monkeypatch.setenv("PROJECT_CONFIG", "true")
    monkeypatch.setenv("PROJECT_CONFIG_ROOTDIR", ROOTDIR_NAME)

    cache_spy = mocker.spy(jmespath_utils.Cache, "get")
    result = jmespath_utils.evaluate_JMESPath(
        jmespath_utils.jmespath_compile(expression),
        instance,
    )
    assert result == expected_result
    assert cache_spy.call_count == 0, "Cache.get() has been called"
