"""Test that project config passes checks for itself."""

from testing_helpers import mark_end2end


@mark_end2end
def test_run_check(capsys):
    """Test that project config passes checks for itself."""
    from project_config.__main__ import run

    exitcode = run(["check"])
    out, err = capsys.readouterr()

    msg = f"{out}\n---\n{err}"
    assert exitcode == 0, msg
    assert out == ""
    assert err == ""
