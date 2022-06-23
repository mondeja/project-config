"""project-config pytest plugin."""

import inspect
import os
import pathlib
import re
import typing as t

import pytest

from project_config.compat import TypeAlias
from project_config.tree import Tree
from project_config.types import Rule, StrictResultType


FilesType: TypeAlias = t.Dict[str, t.Optional[t.Union[str, bool]]]
RootdirType: TypeAlias = t.Union[str, pathlib.Path]


def _create_files(files: FilesType, rootdir: RootdirType) -> None:
    if isinstance(rootdir, pathlib.Path):
        rootdir = str(rootdir)
    for fpath, content in files.items():
        if content is False:
            continue
        full_path = os.path.join(rootdir, fpath)

        if content is None:
            os.mkdir(full_path)
        else:
            content = t.cast(str, content)
            # ensure parent path directory exists
            parent_fpath, _ = os.path.splitext(full_path)
            if parent_fpath:
                os.makedirs(parent_fpath, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)


def _create_tree(
    files: FilesType,
    rootdir: RootdirType,
    cache_files: bool = False,
) -> Tree:
    _create_files(files, rootdir)
    tree = Tree(str(rootdir))
    if cache_files:
        tree.cache_files(list(files))
    return tree


def project_config_plugin_action_asserter(
    plugin_class: type,
    plugin_method_name: str,
    rootdir: RootdirType,
    files: FilesType,
    value: t.Any,
    rule: Rule,
    expected_results: t.List[StrictResultType],
    additional_files: t.Optional[FilesType] = None,
    assert_case_method_name: bool = True,
) -> None:
    """Convenient function to test a plugin action.

    Args:
        plugin_class (type): Plugin class.
        plugin_method_name (str): Plugin method name.
        rootdir (Path): Path to root directory. Is recommended to pass
            the value of the ``tmp_path`` fixture.
        files (dict): Dictionary of files to create.
            Must have the file paths as keys and the content as values.
            The keys will be passed to the ``files`` property of the rule.
            If the value is ``False``, the file will not be created.
            If the value is ``None``, the file will be created as a directory.
        value (typing.Any): Value passed to the action.
        expected_results (list): List of expected results.
        additional_files (dict): Dictionary of additional files to create.
            These will not be defined inside the ``files`` property of the rule.
            Follows the same format as ``files``.
        assert_case_method_name (bool): If ``True``, the method name will
            be checked to match against camelCase or PascalCase style.

    .. rubric:: Example

    .. code-block:: python

       import pytest

       from project_config import Error, InterruptingError, ResultValue
       from project_config.plugins.include import IncludePlugin

       @pytest.mark.parametrize(
           ("files", "value", "rule", "expected_results"),
           (
               pytest.param(
                   {"foo.ext": "foo"},
                   ["foo"],
                   None,
                   [],
                   id="ok",
               ),
               pytest.param(
                   {"foo.ext": "foo"},
                   ["bar"],
                   None,
                   [
                       (
                           Error,
                           {
                               "definition": ".includeLines[0]",
                               "file": "foo.ext",
                               "message": "Expected line 'bar' not found",
                           },
                       ),
                   ],
                   id="error",
               ),
           ),
       )
       def test_includeLines(
           files,
           value,
           rule,
           expected_results,
           tmp_path,
           assert_project_config_plugin_action,
       ):
           assert_project_config_plugin_action(
               IncludePlugin,
               'includeLines',
               tmp_path,
               files,
               value,
               rule,
               expected_results,
           )
    """  # noqa: D417 -> this seems not needed, error in flake8-docstrings?
    if additional_files is not None:
        _create_files(additional_files, rootdir)

    plugin_method = getattr(plugin_class, plugin_method_name)
    results = list(
        plugin_method(
            value,
            _create_tree(files, rootdir, cache_files=True),
            rule,
        ),
    )

    assert re.match(
        r"\w",
        plugin_method_name,
    ), f"Plugin method name '{plugin_method_name}' must be public"

    if assert_case_method_name:
        assert re.match(
            r"[A-Za-z]+((\d)|([A-Z0-9][a-z0-9]+))*([A-Z])?",
            plugin_method_name,
        ), (
            f"Plugin method name '{plugin_method_name}' must be in"
            " camelCase or PascalCase format"
        )

    assert isinstance(
        inspect.getattr_static(plugin_class, plugin_method_name),
        staticmethod,
    ), f"Plugin method '{plugin_method_name}' must be a static method"

    assert len(results) == len(expected_results)

    for (
        (result_type, result_value),
        (expected_result_type, expected_result_value),
    ) in zip(results, expected_results):
        assert result_type == expected_result_type
        assert result_value == expected_result_value


@pytest.fixture  # type: ignore
def assert_project_config_plugin_action() -> t.Any:
    """Pytest fixture to assert a plugin action.

    Returns a function that can be used to assert a plugin action.
    See :py:func:`project_config.tests.pytest_plugin.project_config_plugin_action_asserter`.
    """  # noqa: E501
    return project_config_plugin_action_asserter
