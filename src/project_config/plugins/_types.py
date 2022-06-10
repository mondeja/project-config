import typing as t

from project_config.config.style import RuleType as Rule
from project_config.tree import TreeNodeFilesIterator as Files


ErrorResultType = t.Dict[str, str]
ResultType = str
ResultValue = str
Result = t.Tuple[ErrorResultType, ResultValue]
Results = t.Iterator[Result]

__all__ = (
    "Files",
    "Rule",
    "Results",
)
