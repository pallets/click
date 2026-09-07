import pytest

import click


@pytest.mark.parametrize(
    ("error_message", "expected"),
    [
        ("bad value: nope", "bad value: nope"),
        ("", "nope"),
    ],
)
def test_func_param_type_uses_value_error_message(error_message, expected):
    def parse(value):
        raise ValueError(error_message if error_message else "")

    func_type = click.types._FuncParamType(parse)

    with pytest.raises(click.BadParameter) as exc_info:
        func_type.convert("nope", None, None)

    assert expected in exc_info.value.message
