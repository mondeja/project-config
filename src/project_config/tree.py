"""Cached files tree used by the linter when using checker commands."""

import os
import typing as t
from dataclasses import dataclass

from project_config.serializers import serialize_for_url


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFiles = t.List[t.Tuple[str, TreeNode]]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]
FilePathsArgument = t.Union[t.Iterator[str], t.List[str]]


@dataclass
class Tree:
    """Files cache used by the linter in checking processes.

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

    def _cache_file(self, fpath: str) -> str:
        """Cache a file normalizing its path.

        Args:
            fpath (str): Relative path from root directory.

        Returns:
            str: Normalized absolute path.
        """
        normalized_fpath = os.path.join(self.rootdir, fpath)
        if normalized_fpath not in self.files_cache:
            if os.path.isfile(normalized_fpath):
                with open(normalized_fpath) as f:
                    self.files_cache[normalized_fpath] = f.read()
            elif os.path.isdir(normalized_fpath):
                # recursive generation
                self.files_cache[normalized_fpath] = self._generator(
                    os.path.join(normalized_fpath, fname)
                    for fname in os.listdir(normalized_fpath)
                )
            else:
                # file or directory does not exist
                self.files_cache[normalized_fpath] = None
        return normalized_fpath

    def _generator(self, fpaths: FilePathsArgument) -> TreeNodeFilesIterator:
        for fpath in fpaths:
            yield fpath, self.files_cache[self._cache_file(fpath)]

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

    def serialize_file(self, fpath: str, fcontent: str) -> t.Any:
        """Returns the JSON-serialized version of a file.

        This method is a convenient cache wrapper for
        :py:func:`project_config.serializers.serialize_for_url`.
        Is used by plugin actions which need a JSON-serialized
        version of files to perform operations against them, like
        the ``jmespath`` one.

        Args:
            fpath (str): Path to the file to serialize.
            fcontent (str): Content of the file to serialize as a string.
        """
        # TODO: don't need to pass the file content as second parameter,
        #   retrieve from the plain files cache
        normalized_fpath = os.path.join(self.rootdir, fpath)
        try:
            result = self.serialized_files_cache[normalized_fpath]
        except KeyError:
            result = serialize_for_url(fpath, fcontent)  # type: ignore
            self.serialized_files_cache[normalized_fpath] = result
        return result
