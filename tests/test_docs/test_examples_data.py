import os
import re

from project_config.fetchers.github import get_latest_release_tags
from testing_helpers import mark_end2end, rootdir


@mark_end2end
def test_spdx_license_list_data_version_updated():
    license_list_data_regex = r"spdx/license-list-data@(v[^/]+)/"

    latest_spdx_license_version = get_latest_release_tags(
        "spdx",
        "license-list-data",
    )[0]

    # iterate over all files localed in '{rootdir}/examples' directory
    # and check if they contain a valid SPDX license list data version:
    for root, _, files in os.walk(os.path.join(rootdir, "examples")):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, encoding="utf-8") as f:
                file_content = f.read()
            match = re.search(license_list_data_regex, file_content)
            if match:
                version = match.group(1)
                file_path = os.path.relpath(file_path, rootdir)
                assert version == latest_spdx_license_version, (
                    f"File {file_path} contains an outdated SPDX"
                    f" license list data version: {version}. "
                    "Please update it to the latest version:"
                    f" {latest_spdx_license_version}."
                )
