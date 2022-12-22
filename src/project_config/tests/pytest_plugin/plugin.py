"""project-config pytest plugin."""

from __future__ import annotations

import contextlib
import copy
import functools
import inspect
import os
import pathlib
import re
import types
from typing import TYPE_CHECKING, Any

import pytest

from project_config.constants import InterruptingError, ResultValue
from project_config.tests.pytest_plugin.helpers import (
    assert_expected_files,
    create_files,
    get_reporter_class_from_module,
)
from project_config.types import ActionsContext


if TYPE_CHECKING:
    from project_config.tests.pytest_plugin.helpers import (
        FilesType,
        RootdirType,
    )
    from project_config.types import ErrorDict, Rule, StrictResultType


def project_config_plugin_action_asserter(
    rootdir: RootdirType,
    plugin_class: type,
    plugin_method_name: str,
    files: FilesType,
    value: Any,
    rule: Rule,
    expected_results: list[StrictResultType],
    additional_files: FilesType | None = None,
    assert_case_method_name: bool = True,
    deprecated: bool = False,
    fix: bool = False,
    expected_files: FilesType | None = None,
) -> None:
    """Convenient function to test a plugin action.

    Args:
        rootdir (Path): Path to root directory. This is not needed to define
            in the fixture as is inserted before the execution.
        plugin_class (type): Plugin class.
        plugin_method_name (str): Plugin method name.
        files (dict): Dictionary of files to create.
            Must have the file paths as keys and the content as values.
            The keys will be passed to the ``files`` property of the rule.
            If the value is ``False``, the file will not be created.
            If the value is ``None``, the file will be created as a directory.
        value (typing.Any): Value passed to the action.
        expected_results (list): Expected results.
        additional_files (dict, optional): Dictionary of additional files to
            create. These will not be defined inside the ``files`` property of
            the rule. Follows the same format as ``files``.
        assert_case_method_name (bool, optional): If ``True`` (default), the
            method name will be checked to match against camelCase or
            PascalCase style.
        deprecated (bool, optional): If ``True``, the action must raise a
            deprecation warning. Default value is ``False``.
        fix (bool, optional): If ``True``, the action will be called with
            the ``fix`` mode active. Use ``expected_files`` to check the content
            of the files after the fix is applyed.
        expected_files (dict, optional): Dictionary of expected files.

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
           assert_project_config_plugin_action,
       ):
           assert_project_config_plugin_action(
               IncludePlugin,
               'includeLines',
               files,
               value,
               rule,
               expected_results,
           )
    """  # noqa: D417  (TODO: bug in flake8-docstrings?)
    create_files(files, rootdir)

    if additional_files is not None:
        create_files(additional_files, rootdir)

    assert plugin_method_name not in ("files", "hint"), (
        "Plugin action names can not be 'files' or 'hint' as they are reserved"
        " as special properties for rules."
    )

    plugin_method = getattr(plugin_class, plugin_method_name)

    deprecated_ctx: Any = (
        contextlib.nullcontext if not deprecated else pytest.deprecated_call
    )
    with deprecated_ctx():
        os.chdir(rootdir)

        results = []
        for result_type, result_value in plugin_method(
            value,
            rule,
            ActionsContext(fix=fix, files=list(files)),
        ):
            results.append((result_type, result_value))
            if result_type is InterruptingError or (
                result_type is ResultValue and result_value is False
            ):
                break

    assert re.match(
        r"\w",
        plugin_method_name,
    ), f"Plugin method name '{plugin_method_name}' must be public"

    assert plugin_method_name.isidentifier(), (
        f"Plugin method name '{plugin_method_name}' must be a valid Python"
        " identifier"
    )

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
        assert result_type == expected_result_type, result_value
        assert result_value == expected_result_value

    if expected_files:
        assert_expected_files(expected_files, rootdir)


@pytest.fixture
def assert_project_config_plugin_action(
    tmp_path: pathlib.Path,
) -> Any:
    """Pytest fixture to assert a plugin action.

    Returns a function that can be used to assert a plugin action.
    See :py:func:`project_config.tests.pytest_plugin.plugin.project_config_plugin_action_asserter`.
    """  # noqa: E501
    return functools.partial(project_config_plugin_action_asserter, tmp_path)


def project_config_errors_report_asserter(
    monkeypatch: pytest.MonkeyPatch,
    rootdir: pathlib.Path,
    reporter_module: types.ModuleType,
    errors: list[ErrorDict],
    expected_result: str,
    fmt: str | None = None,
) -> None:
    r"""Asserts an error report from a reporter module.

    Args:
        monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture. This is not
            needed to define in the fixture as is inserted before the execution.
        rootdir (Path): Path to root directory. This is not needed to define
            in the fixture as is inserted before the execution.
        reporters_module (types.ModuleType): Module containing the reporters.
        errors (list): Errors.
        expected_result (str): Expected reported result.

    .. rubric:: Example

    .. code-block:: python

       import pytest

       from project_config.reporters import default

       @pytest.mark.parametrize(
           ("errors", "expected_result"),
           (
               pytest.param(
                   [],
                   "",
                   id="empty",
               ),
               pytest.param(
                   [
                       {
                           "file": "foo.py",
                           "message": "message",
                           "definition": "definition",
                       },
                   ],
                   "foo.py\n  - message definition",
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
                       },
                       {
                           "file": "bar.py",
                           "message": "message 3",
                           "definition": "definition 3",
                       },
                   ],
                   '''foo.py
         - message 1 definition 1
         - message 2 definition 2
       bar.py
         - message 3 definition 3''',
                   id="complex",
               ),
           ),
       )
       def test_default_errors_report(
           errors,
           expected_result,
           assert_errors_report,
       ):
           assert_errors_report(default, errors, expected_result)
    """  # noqa: D417
    BwReporter = get_reporter_class_from_module(reporter_module, color=False)
    bw_reporter = BwReporter(str(rootdir), fmt=fmt)
    for error in copy.deepcopy(errors):
        if "file" in error:
            error["file"] = str(rootdir / error["file"])
        bw_reporter.report_error(error)
    assert bw_reporter.generate_errors_report() == expected_result

    ColorReporter = get_reporter_class_from_module(reporter_module, color=True)
    color_reporter = ColorReporter(str(rootdir), fmt=fmt)
    for error in copy.deepcopy(errors):
        if "file" in error:
            error["file"] = str(rootdir / error["file"])
        color_reporter.report_error(error)
    monkeypatch.setenv("NO_COLOR", "true")  # disable color a moment
    assert color_reporter.generate_errors_report() == expected_result


@pytest.fixture
def assert_errors_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> Any:
    """Pytest fixture to assert errors reports.

    Returns a function that can be used to assert an errors report
    from a reporters module.
    See :py:func:`project_config.tests.pytest_plugin.plugin.project_config_errors_report_asserter`.
    """  # noqa: E501
    return functools.partial(
        project_config_errors_report_asserter,
        monkeypatch,
        tmp_path,
    )


def project_config_data_report_asserter(
    monkeypatch: pytest.MonkeyPatch,
    rootdir: pathlib.Path,
    reporter_module: types.ModuleType,
    data_key: str,
    data: Any,
    expected_result: str,
    fmt: str | None = None,
) -> None:
    r"""Asserts a data report from a reporter module.

    Args:
        monkeypatch (pytest.MonkeyPatch): Monkeypatch fixture. This is not
            needed to define in the fixture as is inserted before the
            execution.
        rootdir (Path): Path to root directory. This is not needed to define
            in the fixture as is inserted before the execution.
        reporters_module (types.ModuleType): Module containing the reporters.
        data_key (str): Data key.
        data (any): Data content to report.
        expected_result (str): Expected reported result.

    .. rubric:: Example

    .. code-block:: python

       import pytest

       from project_config.reporters import default

       @pytest.mark.parametrize(
           ("data_key", "data", "expected_result"),
           (
               pytest.param(
                   "config",
                   {
                       "cache": "5 minutes",
                       "style": "foo.json5",
                   },
                   '''cache: 5 minutes
       style: foo.json5
       ''',
                   id="config-style-string",
               ),
               pytest.param(
                   "style",
                   {
                       "rules": [
                           {
                               "files": ["foo.ext", "bar.ext"],
                           },
                       ],
                   },
                   '''rules:
         - files:
             - foo.ext
             - bar.ext
       ''',
                   id="style-basic",
               ),
           ),
       )
       def test_default_data_report(
           data_key,
           data,
           expected_result,
           assert_data_report,
       ):
           assert_data_report(
               default,
               data_key,
               data,
               expected_result,
           )
    """  # noqa: D417
    BwReporter = get_reporter_class_from_module(reporter_module, color=False)
    bw_reporter = BwReporter(str(rootdir), fmt=fmt)
    assert (
        bw_reporter.generate_data_report(
            data_key,
            copy.deepcopy(data),  # data is probably edited inplace
        )
        == expected_result
    )

    ColorReporter = get_reporter_class_from_module(reporter_module, color=True)
    color_reporter = ColorReporter(str(rootdir), fmt=fmt)
    monkeypatch.setenv("NO_COLOR", "true")
    assert (
        color_reporter.generate_data_report(
            data_key,
            copy.deepcopy(data),
        )
        == expected_result
    )


@pytest.fixture
def assert_data_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> Any:
    """Pytest fixture to assert data reports.

    Returns a function that can be used to assert a data report
    from a reporters module.
    See :py:func:`project_config.tests.pytest_plugin.plugin.project_config_data_report_asserter`.
    """  # noqa: E501
    return functools.partial(
        project_config_data_report_asserter,
        monkeypatch,
        tmp_path,
    )
