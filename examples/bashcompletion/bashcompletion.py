import click
import os

@click.group(chain=True)
def cli():
	pass

@cli.command()
@click.option('-n', is_flag=True)
def cmd1(n):
	pass

@cli.command()
@click.option('-b', is_flag=True)
def cmd2(b):
	pass
