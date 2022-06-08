import os
import typing as t

from typing_extensions import TypeAlias  # Python < 3.9


TreeFile = str
TreeDirectory: TypeAlias = "os._ScandirIterator[str]"
TreeNode = t.Union[TreeFile, TreeDirectory]
TreeNodeFiles = t.Iterator[t.Tuple[str, TreeNode]]


class Tree:
    def __init__(self, rootdir: str) -> None:
        self.rootdir = rootdir
        self.files: t.Dict[str, TreeNode] = {}

    def files_generator(self, fpaths: t.List[str]) -> TreeNodeFiles:
        for fpath in fpaths:
            if fpath not in self.files:
                fcontent: TreeNode = ""
                if os.path.isfile(fpath):
                    with open(fpath) as f:
                        fcontent = f.read()
                elif os.path.isdir(fpath):
                    fcontent = os.scandir(fpath)
                else:
                    # TODO: file must exist
                    continue
                    # TODO: symlinks?

                self.files[fpath] = fcontent
            yield fpath, self.files[fpath]
