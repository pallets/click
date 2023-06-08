from .helpers import assert_no_surrogates
from .helpers import IMPOSSIBLE_UTF8_SURROGATE_STR
from click.exceptions import FileError


def test_file_error_surrogates():
    filename = f"/x/foo{IMPOSSIBLE_UTF8_SURROGATE_STR}.txt"
    exc = FileError(filename=filename)
    message = exc.format_message()
    assert_no_surrogates(message)
    assert message == "Could not open file '/x/foo�.txt': unknown error"
