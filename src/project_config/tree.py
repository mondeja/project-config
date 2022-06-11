import os
import typing as t


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]


class Tree:
    def __init__(self, rootdir: str) -> None:
        self.rootdir = rootdir

        # cache for all files
        #
        # TODO: this type becomes recursive, in the future, define it properly
        # https://github.com/python/mypy/issues/731
        self.files_cache: t.Dict[str, t.Any] = {}

        # latest cached files
        self.files: t.List[t.Any] = []

    def cache_file(self, fpath: str) -> str:
        fpath = os.path.join(self.rootdir, fpath)
        if fpath not in self.files_cache:
            if os.path.isfile(fpath):
                with open(fpath) as f:
                    self.files_cache[fpath] = f.read()
            elif os.path.isdir(fpath):
                # recursive generation
                self.files_cache[fpath] = self.generator(
                    os.path.join(fpath, fname) for fname in os.listdir(fpath)
                )
            else:
                # file or directory does not exist
                self.files_cache[fpath] = None
        return fpath

    def get_file(self, fpath: str) -> TreeNode:
        return self.files_cache[self.cache_file(fpath)]

    def generator(
        self, fpaths: t.Union[t.Iterator[str], t.List[str]]
    ) -> TreeNodeFilesIterator:
        for fpath in fpaths:
            fpath = self.cache_file(fpath)
            yield fpath, self.files_cache[fpath]

    def cache_files(self, fpaths: t.List[str]):
        self.files = list(self.generator(fpaths))
