"""Tests for HelpFormatter.write_usage not breaking options at hyphens.

Regression test for https://github.com/pallets/click/issues/3362
"""

import click


class TestUsageHyphenBreak:
    """Options containing hyphens should not be broken at hyphens."""

    def test_long_options_not_broken_at_hyphens(self):
        """Long options should wrap at word boundaries, not hyphens."""
        options = [
            "--enable-verbose-logging",
            "--output-file-path",
            "--max-retry-count",
        ]
        f = click.HelpFormatter(width=60)
        f.write_usage("program", " ".join(options))
        output = f.getvalue()
        # No option should be broken mid-hyphen
        assert "--max-\n" not in output
        assert "--enable-\n" not in output
        assert "--output-\n" not in output

    def test_wrap_text_no_hyphen_break(self):
        """wrap_text should not break at hyphens by default."""
        text = "enable-verbose-logging output-file-path max-retry-count"
        result = click.wrap_text(text, width=40)
        # Should wrap at spaces, not hyphens
        assert "enable-\n" not in result
        assert "output-\n" not in result

    def test_wrap_text_long_word_preserved(self):
        """A single long word with hyphens should stay intact if it fits."""
        text = "--very-long-option-name-with-many-parts"
        result = click.wrap_text(text, width=80)
        assert result == text

    def test_usage_no_width_no_hyphen_break(self):
        """Even without explicit width, options should not break at hyphens."""
        options = [
            "--enable-verbose-logging",
            "--output-file-path",
            "--max-retry-count",
            "--disable-cache-mode",
            "--config-file-location",
        ]
        f = click.HelpFormatter()
        f.write_usage("program", " ".join(options))
        output = f.getvalue()
        # Verify no option is broken at a hyphen
        for opt in options:
            broken = opt.replace("-", "-\n")
            assert broken not in output, f"Option {opt} was broken at a hyphen"

    def test_wrap_text_normal_text_still_wraps(self):
        """Normal text without hyphens should still wrap correctly."""
        text = "This is a normal sentence that should be wrapped properly."
        result = click.wrap_text(text, width=30)
        lines = result.split("\n")
        # All lines except possibly the last should be <= width
        for line in lines[:-1]:
            assert len(line) <= 30

    def test_usage_starts_correctly(self):
        """Usage line should start with 'Usage: program'."""
        f = click.HelpFormatter(width=65)
        f.write_usage("program", "--enable-verbose-logging --output-file-path")
        output = f.getvalue()
        assert output.startswith("Usage: program")
