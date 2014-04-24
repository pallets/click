import click


@click.group()
@click.option('--repo-home', envvar='REPO_HOME')
def cli(repo_home):
    """Repo is a command line tool that showcases how to build complex
    command line interfaces with Click.
    """
    print('Repo home: %s' % repo_home)


@cli.command()
@click.argument('src')
@click.argument('dest', required=False)
@click.option('--shallow/--deep', default=False,
              help='Makes a checkout shallow or deep.  Deep by default.')
def clone(src, dest, shallow):
    """Clones a repository.

    This will clone the repository at SRC into the folder DEST.  If DEST
    is not provided this will automatically use the last path component
    of SRC and create that folder.
    """
    print('Source: %s' % src)
    print('Destination: %s' % dest)
    print('Shallow: %s' % shallow)


@cli.command()
@click.confirmation_option()
def delete():
    """Deletes a repository.

    This will throw away the current repository.
    """
    print('Deleted')


@cli.command()
@click.option('--username', prompt=True, required=True)
@click.option('--email', prompt='E-Mail', required=True)
@click.password_option()
def setuser(username, email, password):
    """Sets the user credentials.

    This will override the current user config.
    """
    print('Username: %s' % username)
    print('E-Mail: %s' % email)
    print('Password: %s' % ('*' * len(password)))
