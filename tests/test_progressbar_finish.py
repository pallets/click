"""Regression test for pallets/click#3571: progressbar should show full
completion when show_pos=True and update_min_steps doesn't divide length."""

import io

import click


def test_progressbar_finish_shows_full_pos():
    """With length=20, update_min_steps=7, the last 6 intervals
    (20 - 14) must be flushed when finish() is called."""
    bar = click.progressbar(
        range(20),
        show_pos=True,
        update_min_steps=7,
        file=io.StringIO(),
    )
    bar.__enter__()
    for _ in range(20):
        bar.update(1)
    bar.finish()
    assert bar.pos == 20, f"expected pos=20, got {bar.pos}"
    bar.__exit__(None, None, None)
    print("✅ test_progressbar_finish_shows_full_pos passed")


def test_progressbar_finish_evenly_divides():
    """Edge case: update_min_steps divides length exactly — should still work."""
    bar = click.progressbar(
        range(21),
        show_pos=True,
        update_min_steps=7,
        file=io.StringIO(),
    )
    bar.__enter__()
    for _ in range(21):
        bar.update(1)
    bar.finish()
    assert bar.pos == 21, f"expected pos=21, got {bar.pos}"
    bar.__exit__(None, None, None)
    print("✅ test_progressbar_finish_evenly_divides passed")


def test_progressbar_finish_no_update():
    """If no update() is called, finish() should not crash or flush phantom steps."""
    bar = click.progressbar(
        range(20),
        show_pos=True,
        update_min_steps=7,
        file=io.StringIO(),
    )
    bar.__enter__()
    bar.finish()
    # pos starts at 0
    assert bar.pos == 0, f"expected pos=0, got {bar.pos}"
    bar.__exit__(None, None, None)
    print("✅ test_progressbar_finish_no_update passed")


if __name__ == "__main__":
    test_progressbar_finish_shows_full_pos()
    test_progressbar_finish_evenly_divides()
    test_progressbar_finish_no_update()
    print("all passed")
