"""Cached files tree used by the linter when using checker commands."""

from __future__ import annotations

import glob
import os
import typing as t

from project_config.fetchers import fetch
from project_config.serializers import (
    deserialize_for_url,
    guess_preferred_serializer,
    serialize_for_url,
)


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFiles = t.List[t.Tuple[str, TreeNode]]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]
FilePathsArgument = t.Union[t.Iterator[str], t.List[str]]


class Tree:
    """Files cache used by the linter in checking processes.

    It represents the tree of files and directories starting
    at the root directory of the project.

    Instances of :py:class:`project_config.tree.Tree` can be
    iterated with:

    .. code-block:: python

       for fpath, fcontent in tree.files:
           if fcontent is None:
                # file does not exist
                ...
           elif not isinstance(fcontent, str):
                # file is a directory
                #
                # so `fcontent` is another Tree instance here
                for nested_fpath, nested_fcontent in fcontent.files:
                    ...

    If you want to get the serialialized version of the file you can
    use the method :py:meth:`project_config.tree.Tree.serialize_file`:

    .. code-block:: python

       instance = fpath, tree.serialize_file(fpath)

    If you are not inside a context were you have the content
    of the files (a common scenario for conditional actions)
    you can get them calling the method
    :py:meth:`project_config.tree.Tree.get_file_content`:

    .. code-block:: python

       fcontent = tree.get_file_content(fpath)

    This class caches the files contents along with their
    serialized versions, so subsequent access to the same
    files in the project tree are fast.

    Args:
        rootdir (str): Root directory of the project.
    """

    __slots__ = {
        "rootdir",
        "_serialized_files_cache",
        "_files_cache",
        "_files",
    }

    def __init__(self, rootdir: str) -> None:
        self.rootdir = rootdir

        # latest cached files
        self._files: TreeNodeFiles = []

        # cache for all files
        #
        # TODO: this type becomes recursive, in the future, define it properly
        # https://github.com/python/mypy/issues/731
        self._files_cache: t.Dict[str, t.Tuple[bool, t.Optional[str]]] = {}

        # cache for serialized version of files
        #
        # JSON encodable version of files are cached here to avoid
        # multiple calls to serializer for the same file
        self._serialized_files_cache: t.Dict[str, str] = {}

    @property
    def files(self) -> t.List[t.Tuple[str, str]]:
        """Returns an array of the current cached files for a rule action.

        Returns:
            list: Array of tuples with the relative path to the file
                ``rootdir`` as the first item and the content of the file
                as the second one.
        """
        result = []
        for fpath, _content in self._files:
            result.append(
                (
                    os.path.relpath(fpath, self.rootdir)
                    + ("/" if fpath.endswith("/") else ""),
                    _content,
                ),
            )
        return result  # type: ignore

    def normalize_path(self, fpath: str) -> str:
        """Normalize a path given his relative path to the root directory.

        Args:
            fpath (str): Path to the file relative to the root directory.

        Returns:
            str: Normalized absolute path.
        """
        return os.path.join(self.rootdir, fpath)

    def _cache_file(self, fpath: str) -> str:
        """Cache a file normalizing its path.

        Args:
            fpath (str): Relative path from root directory.

        Returns:
            str: Normalized absolute path.
        """
        normalized_fpath = self.normalize_path(fpath)

        if os.path.isfile(normalized_fpath):
            with open(normalized_fpath, encoding="utf-8") as f:
                self._files_cache[normalized_fpath] = (False, f.read())
        elif os.path.isdir(normalized_fpath):
            # recursive generation
            self._files_cache[normalized_fpath] = (  # type: ignore
                True,
                self._generator(
                    os.path.join(normalized_fpath, fname)
                    for fname in os.listdir(normalized_fpath)
                ),
            )
        else:
            # file or directory does not exist
            self._files_cache[normalized_fpath] = (False, None)

        return normalized_fpath

    def _generator(
        self,
        fpaths: FilePathsArgument,
    ) -> t.Iterable[t.Tuple[str, t.Optional[str]]]:
        for fpath_or_glob in fpaths:
            # try to get all existing files from glob
            #
            # note that when a glob does not match any files,
            # is because the file does not exist, so the generator
            # will yield it as is, which would lead to a unexistent
            # file error when an user specifies a glob that do not
            # match any files
            fpaths_from_glob = glob.glob(fpath_or_glob)
            if fpaths_from_glob:
                for fpath in fpaths_from_glob:
                    yield self.normalize_path(fpath), self._files_cache[
                        self._cache_file(fpath)
                    ][1]
            else:
                yield self.normalize_path(fpath_or_glob), self._files_cache[
                    self._cache_file(fpath_or_glob)
                ][1]

    def get_file_content(self, fpath: str) -> str:
        """Returns the content of a file given his relative path.

        This method is tipically used by ``if`` plugin action conditionals
        to get the content of the files that are not defined in ``files``
        subject rules fields.

        Args:
            fpath (str): Path to the file relative to the root directory.
        """
        return self._files_cache[self._cache_file(fpath)][1]  # type: ignore

    def cache_files(self, fpaths: t.List[str]) -> None:
        """Cache a set of files given their paths.

        Args:
            fpaths (list): Paths to the files to store in cache.
        """
        self._files = list(self._generator(fpaths))  # type: ignore

        for fpath, _content in self._files:
            if _content is None:
                if fpath in self._serialized_files_cache:
                    self._serialized_files_cache.pop(fpath)

    def serialize_file(self, fpath: str) -> t.Any:
        """Returns the object-serialized version of a file.

        This method is a convenient cache wrapper for
        :py:func:`project_config.serializers.serialize_for_url`.
        Is used by plugin actions which need an object-serialized
        version of files to perform operations against them, like
        the :ref:`reference/plugins:jmespath` one.

        Args:
            fpath (str): Path to the file to serialize.

        Returns:
            object: Object-serialized version of the file.
        """
        fpath, serializer_name = guess_preferred_serializer(fpath)

        normalized_fpath = self.normalize_path(fpath)
        try:
            result = self._serialized_files_cache[normalized_fpath]
        except KeyError:
            fcontent = self.get_file_content(fpath)
            if fcontent is None:
                raise FileNotFoundError(
                    f"No such file or directory: '{fpath}'",
                )

            result = serialize_for_url(
                fpath,
                fcontent,
                prefer_serializer=serializer_name,
            )
            self._serialized_files_cache[normalized_fpath] = result
        return fpath, result

    def fetch_file(self, url: str) -> t.Any:
        """Fetch a file from online or offline sources given a url or path.

        This method is a convenient cache wrapper for
        :py:func:`project_config.fetchers.fetch`. Used by plugin actions
        which need an object-serialized version of files to perform
        operations against them, like the :ref:`reference/plugins:jmespath`
        one.

        Args:
            url (str): Url or path to the file to fetch.

        Returns:
            object: Object-serialized version of the file.
        """
        try:
            result = self._serialized_files_cache[url]
        except KeyError:
            result = fetch(url)
            self._serialized_files_cache[url] = result

        return result

    def edit_serialized_file(self, fpath: str, new_content: t.Any) -> bool:
        """Edit a file in the cache.

        Args:
            fpath (str): Path to the file to edit.
            new_content (object): New content for the file.

        Returns:
            bool: True if the file content has changed, False otherwise.
        """
        fpath, serializer_name = guess_preferred_serializer(fpath)

        normalized_fpath = self.normalize_path(fpath)
        previous_content_string = self.get_file_content(fpath)
        self._serialized_files_cache[normalized_fpath] = new_content

        new_content_string = deserialize_for_url(
            fpath,
            new_content,
            prefer_serializer=serializer_name,
        )
        self._files_cache[normalized_fpath] = (False, new_content_string)

        if previous_content_string != new_content_string:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content_string)
            return True
        return False
