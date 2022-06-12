import os
import typing as t

from project_config.fetchers import decode_with_decoder, get_decoder


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFiles = t.List[t.Tuple[str, TreeNode]]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]
FilePathsArgument = t.Union[t.Iterator[str], t.List[str]]


class Tree:
    def __init__(self, rootdir: str) -> None:
        self.rootdir = rootdir

        # cache for all files
        #
        # TODO: this type becomes recursive, in the future, define it properly
        # https://github.com/python/mypy/issues/731
        self.files_cache: t.Dict[str, t.Any] = {}

        # cache for decoded version of files
        #
        # JSON encodable version of files are cached here to avoid
        # multiple calls to decoder for the same file
        self.decoded_files_cache: t.Dict[str, str] = {}

        # latest cached files
        self.files: TreeNodeFiles = []

    def cache_file(self, fpath: str) -> t.Tuple[str, str]:
        normalized_fpath = os.path.join(self.rootdir, fpath)
        if normalized_fpath not in self.files_cache:
            if os.path.isfile(normalized_fpath):
                with open(normalized_fpath) as f:
                    self.files_cache[normalized_fpath] = f.read()
            elif os.path.isdir(normalized_fpath):
                # recursive generation
                self.files_cache[normalized_fpath] = self.generator(
                    os.path.join(normalized_fpath, fname)
                    for fname in os.listdir(normalized_fpath)
                )
            else:
                # file or directory does not exist
                self.files_cache[normalized_fpath] = None
        return fpath, normalized_fpath

    def get_file_content(self, fpath: str) -> TreeNode:
        return self.files_cache[self.cache_file(fpath)[1]]  # type: ignore

    def generator(self, fpaths: FilePathsArgument) -> TreeNodeFilesIterator:
        for fpath in fpaths:
            fpath, normalized_fpath = self.cache_file(fpath)
            yield fpath, self.files_cache[normalized_fpath]

    def cache_files(self, fpaths: FilePathsArgument) -> None:
        self.files = list(self.generator(fpaths))

    def decode_file(self, fpath: str, fcontent: str) -> t.Any:
        normalized_fpath = os.path.join(self.rootdir, fpath)
        try:
            result = self.decoded_files_cache[normalized_fpath]
        except KeyError:
            result = decode_with_decoder(fcontent, get_decoder(fpath))
            self.decoded_files_cache[normalized_fpath] = result
        return result
