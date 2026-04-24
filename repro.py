import click


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is not None:
        return


@main.command()
def sub():
    pass


if __name__ == "__main__":
    main()
