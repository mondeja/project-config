"""Cached files tree used by the linter when using checker commands."""

import glob
import os
import typing as t
from dataclasses import dataclass

from project_config.fetchers import fetch
from project_config.serializers import serialize_for_url


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFiles = t.List[t.Tuple[str, TreeNode]]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]
FilePathsArgument = t.Union[t.Iterator[str], t.List[str]]


@dataclass
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

       instance = tree.serialize_file(fpath)

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

    rootdir: str

    def __post_init__(self) -> None:
        # cache for all files
        #
        # TODO: this type becomes recursive, in the future, define it properly
        # https://github.com/python/mypy/issues/731
        self.files_cache: t.Dict[str, t.Any] = {}

        # cache for serialized version of files
        #
        # JSON encodable version of files are cached here to avoid
        # multiple calls to serializer for the same file
        self.serialized_files_cache: t.Dict[str, str] = {}

        # latest cached files
        self.files: TreeNodeFiles = []

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
        if normalized_fpath not in self.files_cache:
            if os.path.isfile(normalized_fpath):
                with open(normalized_fpath, encoding="utf-8") as f:
                    self.files_cache[normalized_fpath] = f.read()
            elif os.path.isdir(normalized_fpath):
                # recursive generation
                self.files_cache[normalized_fpath] = self._generator(
                    self.normalize_path(fname)
                    for fname in os.listdir(normalized_fpath)
                )
            else:
                # file or directory does not exist
                self.files_cache[normalized_fpath] = None
        return normalized_fpath

    def _generator(self, fpaths: FilePathsArgument) -> TreeNodeFilesIterator:
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
                    yield fpath, self.files_cache[self._cache_file(fpath)]
            else:
                yield fpath_or_glob, self.files_cache[
                    self._cache_file(fpath_or_glob)
                ]

    def get_file_content(self, fpath: str) -> TreeNode:
        """Returns the content of a file given his relative path.

        This method is tipically used by ``if`` plugin action conditionals
        to get the content of the files that are not defined in ``files``
        subject rules fields.

        Args:
            fpath (str): Path to the file relative to the root directory.
        """
        return self.files_cache[self._cache_file(fpath)]  # type: ignore

    def cache_files(self, fpaths: FilePathsArgument) -> None:
        """Cache a set of files given their paths.

        Args:
            fpaths (list): Paths to the files to store in cache.
        """
        self.files = list(self._generator(fpaths))

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
        normalized_fpath = self.normalize_path(fpath)
        try:
            result = self.serialized_files_cache[normalized_fpath]
        except KeyError:
            fcontent = self.get_file_content(fpath)
            if fcontent is None:
                raise FileNotFoundError(
                    f"No such file or directory: '{fpath}'",
                )
            result = serialize_for_url(
                fpath,
                fcontent,  # type: ignore
            )
            self.serialized_files_cache[normalized_fpath] = result
        return result

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
            result = self.serialized_files_cache[url]
        except KeyError:
            result = fetch(url)  # type: ignore
            self.serialized_files_cache[url] = result
        return result
