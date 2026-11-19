from __future__ import annotations


def _split_opt(opt: str) -> tuple[str, str]:
    """Splits an option into a prefix and a value."""
    first = opt[:1]
    if first.isalnum():
        return "", opt
    if opt[1:2] == first:
        return opt[:2], opt[2:]
    return first, opt[1:]


def __getattr__(name: str) -> object:
    import warnings

    if name == "split_opt":
        warnings.warn(
            "'parser.split_opt' is deprecated and will be removed in Click 9.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _split_opt

    if name == "split_arg_string":
        from .shell_completion import split_arg_string

        warnings.warn(
            "Importing 'parser.split_arg_string' is deprecated, it will only be"
            " available in 'shell_completion' in Click 9.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return split_arg_string

    raise AttributeError(name)
