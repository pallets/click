#!/usr/bin/env python

import click

@click.group()
def cli():
    return

@cli.group()
def g1():
    return

@cli.group()
def g2():
    return

@g1.command()
def subcmd1():
    return

@g1.command()
def subcmd2():
    return


@g2.command()
def subcmd3():
    return

@g2.command()
def subcmd4():
    return


def test():
    from click._bashcomplete import resolve_ctx
    ctx = resolve_ctx(cli, "hcli", ["g1"])
    assert ctx.command.name == "g1"

    ctx = resolve_ctx(cli, "hcli", ["g2", "subcmd3"])
    assert ctx.command.name == "subcmd3"
    return


if __name__ == '__main__': test()
