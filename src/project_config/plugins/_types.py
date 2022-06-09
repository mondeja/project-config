import typing as t

from project_config.config.style import RuleType as Rule
from project_config.tree import TreeNodeFilesIterator as Files


VerbResult = t.Dict[str, t.List[t.Dict[str, str]]]

__all__ = (
    "Files",
    "Rule",
    "VerbResult",
)
