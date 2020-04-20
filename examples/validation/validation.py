from urllib import parse as urlparse

import click


def validate_count(ctx, param, value):
    if value < 0 or value % 2 != 0:
        raise click.BadParameter("Should be a positive, even integer.")
    return value


class URL(click.ParamType):
    name = "url"

    def convert(self, value, param, ctx):
        if not isinstance(value, tuple):
            value = urlparse.urlparse(value)
            if value.scheme not in ("http", "https"):
                self.fail(
                    f"invalid URL scheme ({value.scheme}). Only HTTP URLs are allowed",
                    param,
                    ctx,
                )
        return value


@click.command()
@click.option(
    "--count", default=2, callback=validate_count, help="A positive even number."
)
@click.option("--foo", help="A mysterious parameter.")
@click.option("--url", help="A URL", type=URL())
@click.version_option()
def cli(count, foo, url):
    """Validation.

    This example validates parameters in different ways.  It does it
    through callbacks, through a custom type as well as by validating
    manually in the function.
    """
    if foo is not None and foo != "wat":
        raise click.BadParameter(
            'If a value is provided it needs to be the value "wat".',
            param_hint=["--foo"],
        )
    click.echo(f"count: {count}")
    click.echo(f"foo: {foo}")
    click.echo(f"url: {url!r}")
