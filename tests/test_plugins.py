from pkg_resources import EntryPoint
from pkg_resources import iter_entry_points
from pkg_resources import working_set

import click


# Create a few CLI commands for testing
@click.command()
@click.argument('arg')
def cmd1(arg):
    """Test command 1"""
    click.echo('passed')

@click.command()
@click.argument('arg')
def cmd2(arg):
    """Test command 2"""
    click.echo('passed')


# Manually register plugins in an entry point and put broken plugins in a
# different entry point.

# The `DistStub()` class gets around an exception that is raised when
# `entry_point.load()` is called.  By default `load()` has `requires=True`
# which calls `dist.requires()` and the `click.group()` decorator
# doesn't allow us to change this.  Because we are manually registering these
# plugins the `dist` attribute is `None` so we can just create a stub that
# always returns an empty list since we don't have any requirements.  A full
# `pkg_resources.Distribution()` instance is not needed because there isn't
# a package installed anywhere.
class DistStub(object):
    def requires(self, *args):
        return []

working_set.by_key['click']._ep_map = {
    'click.test_plugins': {
        'cmd1': EntryPoint.parse(
            'cmd1=tests.test_plugins:cmd1', dist=DistStub()),
        'cmd2': EntryPoint.parse(
            'cmd2=tests.test_plugins:cmd2', dist=DistStub())
    },
    'click.broken_plugins': {
        'before': EntryPoint.parse(
            'before=tests.broken_plugins:before', dist=DistStub()),
        'after': EntryPoint.parse(
            'after=tests.broken_plugins:after', dist=DistStub()),
        'do_not_exist': EntryPoint.parse(
            'do_not_exist=tests.broken_plugins:do_not_exist', dist=DistStub())
    }
}


# Main CLI groups - one with good plugins attached and the other broken
@click.group(plugins=iter_entry_points('click.test_plugins'))
def good_cli():
    """Good CLI group."""
    pass


@click.group(plugins=iter_entry_points('click.broken_plugins'))
def broken_cli():
    """Broken CLI group."""
    pass


def test_registered():
    # Make sure the plugins are properly registered.  If this test fails it
    # means that some of the for loops in other tests may not be executing.
    assert len([ep for ep in iter_entry_points('click.test_plugins')]) > 1
    assert len([ep for ep in iter_entry_points('click.broken_plugins')]) > 1


def test_register_and_run(runner):

    result = runner.invoke(good_cli)
    assert result.exit_code is 0

    for ep in iter_entry_points('click.test_plugins'):
        cmd_result = runner.invoke(good_cli, [ep.name, 'something'])
        assert cmd_result.exit_code is 0
        assert cmd_result.output.strip() == 'passed'


def test_broken_register_and_run(runner):

    result = runner.invoke(broken_cli)
    assert result.exit_code is 0
    assert u'\U0001F4A9' in result.output or u'\u2020' in result.output

    for ep in iter_entry_points('click.broken_plugins'):
        cmd_result = runner.invoke(broken_cli, [ep.name])
        assert cmd_result.exit_code is not 0
        assert 'Traceback' in cmd_result.output


def test_group_chain(runner):

    # Attach a sub-group to a CLI and get execute it without arguments to make
    # sure both the sub-group and all the parent group's commands are present
    @good_cli.group()
    def sub_cli():
        """Sub CLI."""
        pass

    result = runner.invoke(good_cli)
    assert result.exit_code is 0
    assert sub_cli.name in result.output
    for ep in iter_entry_points('click.test_plugins'):
        assert ep.name in result.output

    # Same as above but the sub-group has plugins
    @good_cli.group(plugins=iter_entry_points('click.test_plugins'))
    def sub_cli_plugins():
        """Sub CLI with plugins."""
        pass

    result = runner.invoke(good_cli, ['sub_cli_plugins'])
    assert result.exit_code is 0
    for ep in iter_entry_points('click.test_plugins'):
        assert ep.name in result.output

    # Execute one of the sub-group's commands
    result = runner.invoke(good_cli, ['sub_cli_plugins', 'cmd1', 'something'])
    assert result.exit_code is 0
    assert result.output.strip() == 'passed'
