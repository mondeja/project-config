"""Assert that the jmespath evaluation cache works as expected."""

import os

import pytest
from testing_helpers import mark_end2end

from project_config.utils import jmespath as jmespath_utils


ROOTDIR_NAME = os.path.basename(os.getcwd())


@mark_end2end
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
            r"regex_match('v\d', gh_tags('mondeja', 'project-config')[0])",
            {},
            True,
            id="gh_tags(...)",
        ),
        # TODO: add tests for listdir, isfile, isdir... functions calls
        pytest.param(
            r"listdir",
            {"listdir": "bar"},
            "bar",
            id="listdir",
        ),
        pytest.param(
            r"isfile",
            {"isfile": "bar"},
            "bar",
            id="isfile",
        ),
        pytest.param(
            r"isdir",
            {"isdir": "bar"},
            "bar",
            id="isdir",
        ),
        pytest.param(
            r"exists",
            {"exists": "bar"},
            "bar",
            id="exists",
        ),
        pytest.param(
            r"dirname",
            {"dirname": "bar"},
            "bar",
            id="dirname",
        ),
        pytest.param(
            r"basename",
            {"basename": "bar"},
            "bar",
            id="basename",
        ),
        pytest.param(
            r"extname",
            {"extname": "bar"},
            "bar",
            id="extname",
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

    cache_spy = mocker.spy(jmespath_utils, "Cache")
    result = jmespath_utils.evaluate_JMESPath(
        jmespath_utils.jmespath_compile(expression),
        instance,
    )
    assert result == expected_result
    assert cache_spy.call_count == 0
