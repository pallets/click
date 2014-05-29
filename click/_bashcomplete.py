import os
from click.utils import echo
from click.parser import split_arg_string
from click.core import MultiCommand, Option


COMPLETION_SCRIPT = '''
%(complete_func)s() {
    COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   %(autocomplete_var)s=complete $1 ) )
    return 0
}

complete -F %(complete_func)s -o default %(script_names)s
'''


def get_completion_script(prog_name, complete_var):
    return (COMPLETION_SCRIPT % {
        'complete_func': '_%s_completion' % prog_name,
        'script_names': prog_name,
        'autocomplete_var': complete_var,
    }).strip() + ';'


def resolve_ctx(cli, prog_name, args):
    ctx = cli.make_context(prog_name, args, resilient_parsing=True)
    while ctx.args and isinstance(ctx.command, MultiCommand):
        cmd = ctx.command.get_command(ctx, ctx.args[0])
        if cmd is None:
            return None
        ctx = cmd.make_context(ctx.args[0], ctx.args[1:], parent=ctx,
                               resilient_parsing=True)
    return ctx


def do_complete(cli, prog_name):
    cwords = split_arg_string(os.environ['COMP_WORDS'])
    cword = int(os.environ['COMP_CWORD'])
    args = cwords[1:cword]
    try:
        incomplete = cwords[cword]
    except IndexError:
        incomplete = ''

    ctx = resolve_ctx(cli, prog_name, args)
    if ctx is None:
        return True

    choices = []
    if incomplete and not incomplete[:1].isalnum():
        for param in ctx.command.params:
            if not isinstance(param, Option):
                continue
            choices.extend(param.opts)
            choices.extend(param.secondary_opts)
    elif isinstance(ctx.command, MultiCommand):
        choices.extend(ctx.command.list_commands(ctx))

    for item in choices:
        if item.startswith(incomplete):
            echo(item)

    return True


def bashcomplete(cli, prog_name, complete_var, complete_instr):
    if complete_instr == 'source':
        echo(get_completion_script(prog_name, complete_var))
        return True
    elif complete_instr == 'complete':
        return do_complete(cli, prog_name)
    return False
