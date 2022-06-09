import os
import typing as t


TreeDirectory = t.Iterator[str]
TreeNode = t.Union[str, TreeDirectory]
TreeNodeFilesIterator = t.Iterator[t.Tuple[str, TreeNode]]


class Tree:
    def __init__(self, rootdir: str) -> None:
        self.rootdir = rootdir
        # TODO: this type becomes recursive, in the future, define it properly
        # https://github.com/python/mypy/issues/731
        self.files: t.Dict[str, t.Any] = {}

    def generator(
        self, fpaths: t.Union[t.Iterator[str], t.List[str]]
    ) -> TreeNodeFilesIterator:
        for fpath in fpaths:
            fpath = os.path.join(self.rootdir, fpath)
            if fpath not in self.files:
                if os.path.isfile(fpath):
                    with open(fpath) as f:
                        self.files[fpath] = f.read()
                elif os.path.isdir(fpath):
                    # recursive generation
                    self.files[fpath] = self.generator(
                        os.path.join(fpath, fname) for fname in os.listdir(fpath)
                    )
                # TODO: file must exist
            yield fpath, self.files[fpath]
