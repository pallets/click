import click
from complex.cli import pass_context


@click.command('init', short_help='Initializes a repo.')
@click.argument('path', required=False, type=click.Path(resolve_path=True))
@pass_context
def cli(ctx, path):
    """Initializes a repository."""
    if path is None:
        path = ctx.home
    ctx.log('Initialized the repository in %s',
            click.format_filename(path))
