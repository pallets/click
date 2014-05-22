import click
from complex.cli import pass_context


@click.command('status', short_help='Shows file changes.')
@pass_context
def cli(ctx):
    """Shows file changes in the current working directory."""
    ctx.log('Changed files: none')
    ctx.vlog('bla bla bla, debug info')
