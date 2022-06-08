import typing as t

from project_config.tree import TreeNodeFiles as Files


Rule = t.Any  # TODO: improve this type
VerbResult = t.Dict[str, t.List[t.Dict[str, str]]]

__all__ = (
    "Files",
    "Rule",
    "VerbResult",
)
