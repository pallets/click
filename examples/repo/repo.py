import os
import click


class Repo(object):

    def __init__(self, home):
        self.home = home

    def __repr__(self):
        return '<Repo %r>' % self.home


pass_repo = click.make_pass_decorator(Repo)


@click.group()
@click.option('--repo-home', envvar='REPO_HOME', default='.repo')
@click.pass_context
def cli(ctx, repo_home):
    """Repo is a command line tool that showcases how to build complex
    command line interfaces with Click.
    """
    # Create a repo object and remember it as as the context object.
    ctx.obj = Repo(os.path.abspath(repo_home))


@cli.command()
@click.argument('src')
@click.argument('dest', required=False)
@click.option('--shallow/--deep', default=False,
              help='Makes a checkout shallow or deep.  Deep by default.')
@pass_repo
def clone(repo, src, dest, shallow):
    """Clones a repository.

    This will clone the repository at SRC into the folder DEST.  If DEST
    is not provided this will automatically use the last path component
    of SRC and create that folder.
    """
    print('Repo: %s' % repo)
    print('Source: %s' % src)
    print('Destination: %s' % dest)
    print('Shallow: %s' % shallow)


@cli.command()
@click.confirmation_option()
@pass_repo
def delete(repo):
    """Deletes a repository.

    This will throw away the current repository.
    """
    print('Repo: %s' % repo)
    print('Deleted')


@cli.command()
@click.option('--username', prompt=True, required=True)
@click.option('--email', prompt='E-Mail', required=True)
@click.password_option()
@pass_repo
def setuser(repo, username, email, password):
    """Sets the user credentials.

    This will override the current user config.
    """
    print('Repo: %s' % repo)
    print('Username: %s' % username)
    print('E-Mail: %s' % email)
    print('Password: %s' % ('*' * len(password)))


@cli.command()
@click.option('--message', '-m', required=True, multiple=True)
@pass_repo
def commit(repo, message):
    """Commits outstanding changes."""
    print('Repo: %s' % repo)
    print('\n'.join(message))
    
    
if __name__=="__main__":
    cli()
