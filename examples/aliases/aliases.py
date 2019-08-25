import os
import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


class Config(object):
    """The config in this example only holds aliases."""

    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items('aliases'))
        except configparser.NoSectionError:
            pass


pass_config = click.make_pass_decorator(Config, ensure=True)


class AliasedGroup(click.Group):
    """This subclass of a group supports looking up aliases in a config
    file and with a bit of magic.
    """

    def get_command(self, ctx, cmd_name):
        # Step one: bulitin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Step two: find the config object and ensure it's there.  This
        # will create the config object is missing.
        cfg = ctx.ensure_object(Config)

        # Step three: lookup an explicit command alias in the config
        if cmd_name in cfg.aliases:
            actual_cmd = cfg.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)

        # Alternative option: if we did not find an explicit alias we
        # allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        matches = [x for x in self.list_commands(ctx)
                   if x.lower().startswith(cmd_name.lower())]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def read_config(ctx, param, value):
    """Callback that is used whenever --config is passed.  We use this to
    always load the correct config.  This means that the config is loaded
    even if the group itself never executes so our aliases stay always
    available.
    """
    cfg = ctx.ensure_object(Config)
    if value is None:
        value = os.path.join(os.path.dirname(__file__), 'aliases.ini')
    cfg.read_config(value)
    return value


@click.command(cls=AliasedGroup)
@click.option('--config', type=click.Path(exists=True, dir_okay=False),
              callback=read_config, expose_value=False,
              help='The config file to use instead of the default.')
def cli():
    """An example application that supports aliases."""


@cli.command()
def push():
    """Pushes changes."""
    click.echo('Push')


@cli.command()
def pull():
    """Pulls changes."""
    click.echo('Pull')


@cli.command()
def clone():
    """Clones a repository."""
    click.echo('Clone')


@cli.command()
def commit():
    """Commits pending changes."""
    click.echo('Commit')


@cli.command()
@pass_config
def status(config):
    """Shows the status."""
    click.echo('Status for %s' % config.path)
