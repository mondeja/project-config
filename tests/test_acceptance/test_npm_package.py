import os
import shutil
import subprocess

from testing_helpers import mark_end2end, mark_linux_only, rootdir


@mark_end2end
@mark_linux_only
def test_npm_pack_and_install(tmp_path):
    packer_dir = tmp_path / "packer"
    user_dir = tmp_path / "user"
    user_dir.mkdir()

    package_src_dir = os.path.join(rootdir, "contrib", "npm")
    shutil.copytree(package_src_dir, packer_dir)

    proc = subprocess.run(
        ["npm", "pack"],
        check=True,
        cwd=packer_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert proc.returncode == 0

    tgz_filename = list(
        filter(
            lambda name: name.startswith("python-project-config"),
            os.listdir(packer_dir),
        ),
    )[0]
    tgz_path = packer_dir / tgz_filename
    assert os.path.isfile(tgz_path)

    proc = subprocess.run(
        ["npm", "init", "-y"],
        check=True,
        cwd=user_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert proc.returncode == 0

    proc = subprocess.run(
        ["npm", "i", tgz_path],
        check=True,
        cwd=user_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    package_json_file = user_dir / "package.json"
    assert (
        '"python-project-config": "file:../packer/python-project-config-'
    ) in package_json_file.read_text()

    assert proc.returncode == 0
