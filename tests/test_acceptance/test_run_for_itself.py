"""Test that project config passes checks for itself."""

from testing_helpers import mark_end2end


@mark_end2end
def test_run_check():
    """Test that project config passes checks for itself."""
    from project_config.__main__ import run

    assert run(["check"]) == 0
