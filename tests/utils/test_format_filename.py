from click import format_filename


def test_filename_formatting():
    assert format_filename(b"foo.txt") == "foo.txt"
    assert format_filename(b"/x/foo.txt") == "/x/foo.txt"
    assert format_filename("/x/foo.txt") == "/x/foo.txt"
    assert format_filename("/x/foo.txt", shorten=True) == "foo.txt"
    assert format_filename("/x/\ufffd.txt", shorten=True) == "�.txt"
