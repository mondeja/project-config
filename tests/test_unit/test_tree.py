"""Tests for on-demand files/directories tree iterator."""

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
    assert tree._files_cache == {}  # files are cached when used
    assert isinstance(files, types.GeneratorType)

    assert next(files) == (str(path), expected_content)
    assert tree._files_cache == {str(path): (False, expected_content)}

    with pytest.raises(StopIteration):
        next(files)


def test_Tree_file_caching(tmp_path):
    """Tree cache is working."""
    expected_content = "bar"
    path = tmp_path / "foo"
    path.write_text(expected_content)

    tree = Tree(tmp_path)
    tree._files_cache = TreeFilesCacheListenerMock()

    expected_files = {str(path): (False, expected_content)}
    files1 = tree._generator([path.name])
    assert tree._files_cache == {}
    assert tree._files_cache.setitem_calls == 0
    next(files1)
    assert tree._files_cache.setitem_calls == 1
    assert tree._files_cache == expected_files

    files2 = tree._generator([path.name])
    next(files2)
    assert tree._files_cache.setitem_calls == 2  # no more __setitem__
    assert tree._files_cache == expected_files


def test_Tree_directory(tmp_path):
    foo_path = tmp_path / "foo"
    foo_path.mkdir()

    bar_path = foo_path / "bar.txt"
    bar_path.write_text("bar")

    baz_path = foo_path / "baz.txt"
    baz_path.write_text("baz")

    tree = Tree(tmp_path)
    tree._files_cache = TreeFilesCacheListenerMock()

    directory_generator = tree._generator([foo_path.name])
    assert isinstance(directory_generator, types.GeneratorType)

    foo_fpath, foo_fcontent = next(directory_generator)
    assert foo_fpath == str(foo_path)
    assert isinstance(foo_fcontent, types.GeneratorType)
    assert tree._files_cache.setitem_calls == 1

    # files from directory
    fpath, fcontent = next(foo_fcontent)
    assert fpath in (str(baz_path), str(bar_path))
    assert fcontent in ("baz", "bar")
    assert tree._files_cache.setitem_calls == 2

    fpath, fcontent = next(foo_fcontent)
    assert fpath in (str(baz_path), str(bar_path))
    assert fcontent in ("baz", "bar")
    assert tree._files_cache.setitem_calls == 3

    with pytest.raises(StopIteration):
        next(foo_fcontent)


def test_file_symlink(tmp_path):
    """Symlinks must be handled as normal files."""
    source_link_path = tmp_path / "source"
    target_link_path = tmp_path / "target"

    target_link_path.write_text("target")

    source_link_path.symlink_to(target_link_path)
    assert source_link_path.read_text() == "target"

    tree = Tree(tmp_path)
    tree._files_cache = TreeFilesCacheListenerMock()

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
        tree._files_cache = TreeFilesCacheListenerMock()

        generator = tree._generator(["**/*"])
        assert isinstance(generator, types.GeneratorType)

        def assert_file(_fpath, _fcontent):
            if _fcontent == "bar":
                assert str(_fpath) == str(bar_path)
                assert _fcontent == "bar"
            else:
                assert str(_fpath) == str(baz_path)
                assert _fcontent == "baz"

        fpath, fcontent = next(generator)
        assert_file(fpath, fcontent)
        assert tree._files_cache.setitem_calls == 1

        fpath, fcontent = next(generator)
        assert_file(fpath, fcontent)
        assert tree._files_cache.setitem_calls == 2

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
        tree._files_cache = TreeFilesCacheListenerMock()

        generator = tree._generator(["*"])
        assert isinstance(generator, types.GeneratorType)

        fpath1, fcontent = next(generator)
        if "source" in str(fpath1):
            # source and target files order are not the same between platforms
            assert str(fpath1) == str(source_link_path)
        else:
            assert str(fpath1) == str(target_link_path)
        assert fcontent == "target"
        assert tree._files_cache.setitem_calls == 1

        fpath2, fcontent = next(generator)
        if "source" in str(fpath2):
            assert str(fpath2) == str(source_link_path)
        else:
            assert str(fpath2) == str(target_link_path)
        assert fcontent == "target"
        assert tree._files_cache.setitem_calls == 2

        assert fpath1 != fpath2  # globbing does not resolve symlink paths

        with pytest.raises(StopIteration):
            next(generator)


def test_serialize_unexistent_file(tmp_path, chdir):
    tree = Tree(str(tmp_path))
    with chdir(tmp_path):
        with pytest.raises(
            FileNotFoundError,
            match=r"No such file or directory: 'foo\.ext'",
        ):
            tree.serialize_file("foo.ext")
