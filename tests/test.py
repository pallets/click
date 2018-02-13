#!/usr/bin/env python

import click

def _complete(ctx, args, incomplete):
    return ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqr', 'stu', 'vwx', 'yz']

@click.group()
def entrypoint():
    pass

@click.command()
@click.option('--opt', autocompletion=_complete)
@click.argument('arg', nargs=-1)
def subcommand(opt, arg):
    pass

entrypoint.add_command(subcommand)

entrypoint()