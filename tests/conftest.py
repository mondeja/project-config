import os

import pytest
from contextlib_chdir import chdir as chdir_ctx

from project_config import Tree


@pytest.fixture
def chdir():
    return chdir_ctx


def _assert_minimal_valid_config(config, expected_style="foo"):
    assert isinstance(config, dict)
    assert len(config) == 1
    assert config["style"] == expected_style


def _minimal_valid_config_with_style(value):
    return f"style = '{value}'"


default_minimal_valid_config_string = _minimal_valid_config_with_style("foo")


@pytest.fixture
def minimal_valid_config():
    min_valid_config = type(
        "MinimalValidConfig",
        (),
        {
            "asserts": _assert_minimal_valid_config,
            "with_style": _minimal_valid_config_with_style,
        },
    )
    min_valid_config.string = default_minimal_valid_config_string
    return min_valid_config


def _assert_minimal_valid_style(value):
    pass


@pytest.fixture
def minimal_valid_style():
    min_valid_style = type(
        "MinimalValidStyle",
        (),
        {
            "asserts": _assert_minimal_valid_style,
        },
    )
    min_valid_style.string = '{"rules": [{"files": ["foo"]}]}'
    return min_valid_style


def _create_files(files, rootdir):
    for fpath, content in files.items():
        full_path = rootdir / fpath
        if content is None:
            full_path.mkdir()
        else:
            # ensure parent path directory exists
            parent_fpath, filename = os.path.splitext(str(full_path))
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)
            full_path.write_text(content)


def _create_tree(files, rootdir, cache_files=False):
    _create_files(files, rootdir)
    tree = Tree(rootdir)
    if cache_files:
        tree.cache_files(list(files))
    return tree


@pytest.fixture
def create_files():
    return _create_files


@pytest.fixture
def create_tree():
    return _create_tree


def _assert_plugin_action(
    plugin_method,
    rootdir,
    files,
    value,
    rule,
    expected_results,
):
    results = list(
        plugin_method(
            value,
            _create_tree(files, rootdir, cache_files=True),
            rule,
        ),
    )

    assert len(results) == len(expected_results)

    for (
        (result_type, result_value),
        (expected_result_type, expected_result_value),
    ) in zip(results, expected_results):
        assert result_type == expected_result_type
        assert result_value == expected_result_value


@pytest.fixture
def assert_plugin_action():
    return _assert_plugin_action
