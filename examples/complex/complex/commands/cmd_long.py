import click
from complex.cli import pass_context


@click.command('long', context_settings={'max_content_width': 700}, help='Shows a realy long message meant for the purposes of debugging the short help default option shortener function in util'*20)
@pass_context
def cli(ctx):
    """Shows file changes in the current working directory."""
    ctx.log('long: stuff happened')
    ctx.vlog('bla bla bla, volatile long long long long long long unsigned debug info')
