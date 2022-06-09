import json
import os
import typing as t

from project_config.config.style.fetchers import FetchResult

def fetch(url: str) -> FetchResult:
    with open(os.path.expanduser(url)) as f:
        return f.read()
