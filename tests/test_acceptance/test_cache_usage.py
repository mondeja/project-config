import importlib
import os
import sys
from unittest import mock

import pytest


@mock.patch.dict(os.environ, {"PROJECT_CONFIG_USE_CACHE": "false"})
def test_use_noop_cache():
    """When the environment variable 'PROJECT_CONFIG_USE_CACHE' is set
    to 'false' the cache is disabled.
    """
    if "project_config.cache" in sys.modules:
        del sys.modules["project_config.cache"]

    project_config_cache = importlib.import_module("project_config.cache")

    assert not hasattr(project_config_cache.Cache, "_cache")

    del sys.modules["project_config.cache"]


@pytest.mark.parametrize("value", ("", "true", "0"))
def test_use_cache(value):
    """When the environment variable 'PROJECT_CONFIG_USE_CACHE' is set
    to 'false' the cache is disabled.
    """
    if "project_config.cache" in sys.modules:
        del sys.modules["project_config.cache"]

    with mock.patch.dict(os.environ, {"PROJECT_CONFIG_USE_CACHE": value}):
        project_config_cache = importlib.import_module("project_config.cache")

        assert hasattr(project_config_cache.Cache, "_cache")

    del sys.modules["project_config.cache"]
