import pytest
from testing_helpers import mark_end2end

from project_config.__main__ import run
from project_config.cache import Cache
from project_config.config import Config
from project_config.config.style import (
    ProjectConfigInvalidStyle,
    _prefetch_urls,
)
from project_config.plugins import Plugins


@pytest.mark.parametrize(
    ("files", "expected_result"),
    (
        pytest.param(
            {
                ".project-config.toml": 'style = "style.json5"',
            },
            ["style -> 'style.json5' file not found"],
            id="fetch-style-error",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = ["style.json5"]',
            },
            ["style[0] -> 'style.json5' file not found"],
            id="fetch-styles-error",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = ["style.json5"]',
                "style.json5": '{ extends: ["bar.json"] }',
            },
            [
                "style.json5: .extends[0] -> 'bar.json' file not found",
            ],
            id="fetch-extend-styles-error",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "style.json5"',
                "style.json5": "{}",
            },
            ["style.json5: .rules or .extends -> one of both is required"],
            id="missing-rules",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "style.json5"',
                "style.json5": "{ rules: [] }",
            },
            ["style.json5: .rules -> at least one rule is required"],
            id="empty-rules",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ extends: ["bar.json5"] }',
                "bar.json5": (
                    '{ rules: [{files: ["baz.txt"], includeLines: ["baz"]}] }'
                ),
            },
            {
                "plugins": [],
                "rules": [{"files": ["baz.txt"], "includeLines": ["baz"]}],
            },
            id="extend-partial-style",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ extends: ["bar.json5"] }',
                "bar.json5": "{ rules: [] }",
            },
            [
                "bar.json5: .rules -> at least one rule is required",
            ],
            id="extend-partial-style-empty-rules",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ extends: ["bar.json5"] }',
                "bar.json5": '{ extends: ["baz.json5"] }',
                "baz.json5": "{ rules: [] }",
            },
            [
                "baz.json5: .rules -> at least one rule is required",
            ],
            id="multiple-extends",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: ["inclusion"],'
                    ' rules: [{files: [".gitignore"]}] }'
                ),
            },
            {"plugins": ["inclusion"], "rules": [{"files": [".gitignore"]}]},
            id="plugin",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: [], rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .plugins -> must not be empty"],
            id="empty-plugins",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: 5, rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .plugins -> must be of type array"],
            id="invalid-plugins-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: ["inclusion", 5],'
                    ' rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .plugins[1] -> must be of type string"],
            id="invalid-plugin-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: ["inclusion", ""],'
                    ' rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .plugins[1] -> must not be empty"],
            id="empty-plugin",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ plugins: ["plugin-that-does-not-exist"],'
                    ' rules: [{files: [".gitignore"]}] }'
                ),
            },
            {  # The plugin is loaded on demand, does not raises an error here
                "plugins": ["plugin-that-does-not-exist"],
                "rules": [{"files": [".gitignore"]}],
            },
            id="not-existent-plugin",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ extends: [], rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .extends -> must not be empty"],
            id="empty-extends",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ extends: [""], rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .extends[0] -> must not be empty"],
            id="empty-extend",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ extends: 5, rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .extends -> must be of type array"],
            id="invalid-extends-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ extends: [5], rules: [{files: [".gitignore"]}] }'
                ),
            },
            ["foo.json5: .extends[0] -> must be of type string"],
            id="invalid-extend-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: 5 }",
            },
            ["foo.json5: .rules -> must be of type array"],
            id="invalid-rules-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: [5] }",
            },
            ["foo.json5: .rules[0] -> must be of type object"],
            id="invalid-rule-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: [{}] }",
            },
            ["foo.json5: .rules[0].files -> is required"],
            id="invalid-rule-missing-files",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: [{files: 5}] }",
            },
            ["foo.json5: .rules[0].files -> must be of type array or object"],
            id="rule-invalid-files-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: [{files: []}] }",
            },
            ["foo.json5: .rules[0].files -> at least one file is required"],
            id="rule-invalid-empty-files",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: [""]}] }',
            },
            ["foo.json5: .rules[0].files[0] -> must not be empty"],
            id="rule-invalid-empty-file",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: ["bar", 5]}] }',
            },
            ["foo.json5: .rules[0].files[1] -> must be of type string"],
            id="rule-invalid-file-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {other: ""}}] }',
            },
            [
                (
                    "foo.json5: .rules[0].files -> when files is an object,"
                    " must have one 'not' key"
                ),
            ],
            id="rule-files-object-missing-not",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {not: ""}}] }',
            },
            [
                (
                    "foo.json5: .rules[0].files.not"
                    " -> must be of type array or object"
                ),
            ],
            id="rule-files-not-invalid-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": "{ rules: [{files: {not: []}}] }",
            },
            ["foo.json5: .rules[0].files.not -> must not be empty"],
            id="rule-files-empty-not",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ rules: [{files: {not: {"": "Because bar"}}}] }'
                ),
            },
            [
                (
                    "foo.json5: .rules[0].files.not['']"
                    " -> file path must not be empty"
                ),
            ],
            id="rule-files-not-object-invalid-empty-path",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {not: {"bar.json": ""}}}] }',
            },
            {"rules": [{"files": {"not": {"bar.json": ""}}}]},
            id="rule-files-not-object-empty-reason",  # ok
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {not: {"bar.json": 5}}}] }',
            },
            [
                (
                    "foo.json5: .rules[0].files.not.bar.json"
                    " -> must be of type string"
                ),
            ],
            id="rule-files-not-object-invalid-reason-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {not: ["bar.json", 5]}}] }',
            },
            ["foo.json5: .rules[0].files.not[1] -> must be of type string"],
            id="rule-files-not-array-invalid-path-type",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: {not: ["bar.json", ""]}}] }',
            },
            ["foo.json5: .rules[0].files.not[1] -> must not be empty"],
            id="rule-files-not-array-invalid-empty-path",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ rules: [{files: {not: ["bar.json"]},'
                    ' "includeLines": ["foo bar"]}] }'
                ),
            },
            [
                (
                    "foo.json5: .rules[0] -> when requiring absence of files"
                    " with '.files.not', no other actions can be used in the"
                    " same rule"
                ),
            ],
            id="rule-files-not-other-action",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": '{ rules: [{files: ["bar"], "": 5}] }',
            },
            ["foo.json5: .rules[0].'' -> action must not be empty"],
            id="rule-invalid-empty-action",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = "foo.json5"',
                "foo.json5": (
                    '{ rules: [{files: ["bar"],'
                    ' "actionFooBarBazThatShouldNotExist": 5}] }'
                ),
            },
            [
                (
                    "foo.json5: .rules[0].actionFooBarBazThatShouldNotExist"
                    " -> invalid action, not found in defined plugins:"
                    f" {', '.join(Plugins().plugin_names)}"
                ),
            ],
            id="rule-not-existent-action",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = ["foo.json5"]',
                "foo.json5": '{ extends: ["bar.yaml"] }',
                "bar.yaml": "{ rules: 1, extends: 1 }",
            },
            [
                "bar.yaml: .extends -> must be of type array",
                "bar.yaml: .rules -> must be of type array",
            ],
            # NOTE: bug in coverage here, it marks the `else` branch
            #   as not reached
            id="invalid-partial-style",
        ),
        pytest.param(
            {
                ".project-config.toml": 'style = ["foo.py"]',
                "foo.py": (
                    # this style must be in a Python file because
                    # it allows integers as keys in objects (dicts)
                    'rules = [{"files": {"not": {1: "foo"}}}]'
                ),
            },
            [
                (
                    "foo.py: .rules[0].files.not[1] -> file path must"
                    " be of type string"
                ),
            ],
            id="rule-not-object-invalid-key-type",
        ),
    ),
)
def test_load_style(tmp_path, create_files, chdir, files, expected_result):
    if ".project-config.toml" not in files and "pyproject.toml" not in files:
        raise NotImplementedError(
            "Not implemented loading styles in test with no default"
            " configuration file created",
        )
    create_files(files, tmp_path)

    with chdir(tmp_path):

        if isinstance(expected_result, list):
            expected_result = [
                message.replace("{rootdir}", str(tmp_path))
                for message in expected_result
            ]
            config = Config(str(tmp_path), None)
            with pytest.raises(ProjectConfigInvalidStyle) as exc:
                config.load_style()
            assert exc.value.args[0] == (
                ".project-config.toml"
                if ".project-config.toml" in files
                else "pyproject.toml"
            ), exc.value
            assert exc.value.args[1] == expected_result
        else:
            config = Config(str(tmp_path), None)
            config.load_style()
            assert config.dict_["style"] == expected_result


class FakeConfig:
    def __init__(self, rootdir, dict_):
        self.dict_ = dict_
        self.rootdir = rootdir

    def __getitem__(self, key):
        return self.dict_[key]


@mark_end2end
def test__prefetch_urls_local_files(tmp_path, mocker, capsys, monkeypatch):
    assert run(["clean", "cache"]) == 0
    capsys.readouterr()

    monkeypatch.setenv("PROJECT_CONFIG_USE_CACHE", "true")

    extended_style_file = tmp_path / "bar.yaml"
    extended_style_file.write_text("")

    style_file = tmp_path / "foo.yaml"
    style_file.write_text(f"extends:\n  - {str(extended_style_file)}\n")

    cache_getter_spy = mocker.spy(Cache, "get")

    _prefetch_urls(
        FakeConfig(
            str(tmp_path),
            {
                "style": str(style_file),
            },
        ),
    )
    _prefetch_urls(
        FakeConfig(
            str(tmp_path),
            {
                "style": [str(style_file)],
            },
        ),
    )

    # all are local files, don't fetch
    assert cache_getter_spy.call_count == 0


@mark_end2end
def test__prefetch_urls_remote_files(tmp_path, mocker, monkeypatch, capsys):
    assert run(["clean", "cache"]) == 0
    capsys.readouterr()

    monkeypatch.setenv("PROJECT_CONFIG_USE_CACHE", "true")

    cache_getter_spy = mocker.spy(Cache, "get")
    cache_setter_spy = mocker.spy(Cache, "set")

    _prefetch_urls(
        FakeConfig(
            str(tmp_path),
            {
                "style": (
                    "gh://mondeja/project-config"
                    "/tests/data/styles/bar/style-2.yaml"
                ),
            },
        ),
    )
    _prefetch_urls(
        FakeConfig(
            str(tmp_path),
            {
                "style": [
                    (
                        "gh://mondeja/project-config"
                        "/tests/data/styles/foo/style-1.json5"
                    ),
                ],
            },
        ),
    )

    # all are local files, don't fetch
    assert cache_getter_spy.call_count == 6
    assert cache_setter_spy.call_count == 3
