import sys


if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

tomllib_package_name = "tomli" if sys.version_info < (3, 11) else "tomllib"

__all__ = (
    "Protocol",
    "TypeAlias",
    "tomllib_package_name",
)
