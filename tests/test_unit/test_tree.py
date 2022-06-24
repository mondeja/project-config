"""Tests for on-demand files/directories tree iterator."""

import collections.abc
import types

import pytest

from project_config.tree import Tree


class TreeFilesCacheListenerMock(dict):
    def __init__(self, *args, **kwargs):
        self.setitem_calls = 0
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.setitem_calls += 1
        super().__setitem__(key, value)


def test_Tree_generator(tmp_path):
    """File exists, we can access to their content."""
    expected_content = "bar"
    path = tmp_path / "foo"

    path.write_text(expected_content)

    tree = Tree(tmp_path)
    assert tree.rootdir == tmp_path

    files = tree._generator([path.name])  # paths relative to rootdir
    assert tree.files_cache == {}  # files are cached when used
    assert isinstance(files, types.GeneratorType)

    assert next(files) == (path.name, expected_content)
    assert tree.files_cache == {str(path): expected_content}

    with pytest.raises(StopIteration):
        next(files)


def test_Tree_file_caching(tmp_path):
    """Tree cache is working."""
    expected_content = "bar"
    path = tmp_path / "foo"
    path.write_text(expected_content)

    tree = Tree(tmp_path)
    tree.files_cache = TreeFilesCacheListenerMock()

    expected_files = {str(path): expected_content}
    files1 = tree._generator([path.name])
    assert tree.files_cache == {}
    assert tree.files_cache.setitem_calls == 0
    next(files1)
    assert tree.files_cache.setitem_calls == 1
    assert tree.files_cache == expected_files

    files2 = tree._generator([path.name])
    next(files2)
    assert tree.files_cache.setitem_calls == 1  # no more __setitem__
    assert tree.files_cache == expected_files


def test_Tree_directory(tmp_path):
    dir_path = tmp_path / "foo"
    dir_path.mkdir()

    bar_path = dir_path / "bar"
    bar_path.write_text("bar")

    baz_path = dir_path / "baz"
    baz_path.write_text("baz")

    tree = Tree(tmp_path)
    tree.files_cache = TreeFilesCacheListenerMock()

    # directory generator
    directory_generator = tree._generator([dir_path.name])
    assert isinstance(directory_generator, types.GeneratorType)

    fpath, fcontent = next(directory_generator)
    assert fpath == dir_path.name
    assert isinstance(fcontent, collections.abc.Iterable)
    assert tree.files_cache.setitem_calls == 1

    # files from directory
    bar_fpath, bar_fcontent = next(fcontent)
    bar_fpath == bar_path.name
    bar_fcontent == "bar"
    assert tree.files_cache.setitem_calls == 2

    baz_fpath, baz_fcontent = next(fcontent)
    baz_fpath == baz_path.name
    baz_fcontent == "baz"
    assert tree.files_cache.setitem_calls == 3

    with pytest.raises(StopIteration):
        next(fcontent)


def test_file_symlink(tmp_path):
    """Symlinks must be handled as normal files."""
    source_link_path = tmp_path / "source"
    target_link_path = tmp_path / "target"

    target_link_path.write_text("target")

    source_link_path.symlink_to(target_link_path)
    assert source_link_path.read_text() == "target"

    tree = Tree(tmp_path)
    tree.files_cache = TreeFilesCacheListenerMock()

    generator = tree._generator([str(target_link_path), str(source_link_path)])

    target_fpath, target_fcontent = next(generator)
    assert str(target_fpath) == str(target_link_path)
    assert target_fcontent == "target"

    source_fpath, source_fcontent = next(generator)
    assert str(source_fpath) == str(source_link_path)
    assert source_fcontent == "target"

    with pytest.raises(StopIteration):
        next(generator)


def test_glob(tmp_path, chdir):
    """Globbing works."""
    with chdir(tmp_path):  # globbing only works from rootdir
        dir_path = tmp_path / "foo"
        dir_path.mkdir()

        bar_path = dir_path / "bar"
        bar_path.write_text("bar")
        baz_path = dir_path / "baz"
        baz_path.write_text("baz")

        tree = Tree(tmp_path)
        tree.files_cache = TreeFilesCacheListenerMock()

        generator = tree._generator(["**/*"])
        assert isinstance(generator, types.GeneratorType)

        def assert_file(_fpath, _fcontent):
            if _fcontent == "bar":
                assert str(_fpath) == str(bar_path.relative_to(tmp_path))
                assert _fcontent == "bar"
            else:
                assert str(_fpath) == str(baz_path.relative_to(tmp_path))
                assert _fcontent == "baz"

        fpath, fcontent = next(generator)
        assert_file(fpath, fcontent)
        assert tree.files_cache.setitem_calls == 1

        fpath, fcontent = next(generator)
        assert_file(fpath, fcontent)
        assert tree.files_cache.setitem_calls == 2

        with pytest.raises(StopIteration):
            next(generator)


def test_glob_with_symlink(tmp_path, chdir):
    """Globbing works with symlinks."""
    with chdir(tmp_path):
        source_link_path = tmp_path / "source"
        target_link_path = tmp_path / "target"

        target_link_path.write_text("target")

        source_link_path.symlink_to(target_link_path)
        assert source_link_path.read_text() == "target"

        tree = Tree(tmp_path)
        tree.files_cache = TreeFilesCacheListenerMock()

        generator = tree._generator(["*"])
        assert isinstance(generator, types.GeneratorType)

        fpath1, fcontent = next(generator)
        if "source" in str(fpath1):
            # source and target files order are not the same between platforms
            assert str(fpath1) == str(source_link_path.relative_to(tmp_path))
        else:
            assert str(fpath1) == str(target_link_path.relative_to(tmp_path))
        assert fcontent == "target"
        assert tree.files_cache.setitem_calls == 1

        fpath2, fcontent = next(generator)
        if "source" in str(fpath2):
            assert str(fpath2) == str(source_link_path.relative_to(tmp_path))
        else:
            assert str(fpath2) == str(target_link_path.relative_to(tmp_path))
        assert fcontent == "target"
        assert tree.files_cache.setitem_calls == 2

        assert fpath1 != fpath2  # globbing does not resolve symlink paths

        with pytest.raises(StopIteration):
            next(generator)
