`_AtomicFile.close()` accepts a `delete` parameter, and `__exit__` passes `delete=True` when an exception occurs during the context manager block. However, the `close` method unconditionally calls `os.replace`, moving the (potentially incomplete) temp file over the original regardless of whether `delete` is `True`.

This defeats the purpose of atomic writes — if an error occurs while writing, the original file should be preserved and the temp file should be cleaned up instead.

This change makes `close` check the `delete` flag. When `True`, it removes the temp file with `os.unlink` rather than replacing the original. The `os.unlink` call is wrapped in a try/except to handle cases where the temp file may have already been removed.
