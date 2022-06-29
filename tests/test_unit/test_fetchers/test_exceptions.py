import pytest

from project_config.fetchers import (
    SchemeProtocolNotImplementedError,
    fetch,
    resolve_maybe_relative_url,
)


def test_fetch_not_implemented_protocol_error():
    with pytest.raises(SchemeProtocolNotImplementedError) as exc:
        fetch("foobar://example.com")
    assert exc.value.message == (
        "Fetching from scheme protocol 'foobar:' is not implemented."
    )


def test_resolve_maybe_relative_url_parent_protocol_error(tmp_path):
    with pytest.raises(SchemeProtocolNotImplementedError, match="foobar"):
        resolve_maybe_relative_url(
            "example.txt",
            "foobar://example.com",
            str(tmp_path),
        )
