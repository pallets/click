import os
import re
from .utils import echo
from .parser import split_arg_string
from .core import MultiCommand, Option


COMPLETION_SCRIPT = '''
%(complete_func)s() {
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   %(autocomplete_var)s=complete $1 ) )
    return 0
}

complete -F %(complete_func)s -o default %(script_names)s
'''

_invalid_ident_char_re = re.compile(r'[^a-zA-Z0-9_]')


def get_completion_script(prog_name, complete_var):
    cf_name = _invalid_ident_char_re.sub('', prog_name.replace('-', '_'))
    return (COMPLETION_SCRIPT % {
        'complete_func': '_%s_completion' % cf_name,
        'script_names': prog_name,
        'autocomplete_var': complete_var,
    }).strip() + ';'


def resolve_ctx(cli, prog_name, args):
    ctx = cli.make_context(prog_name, args, resilient_parsing=True)
    args_remaining = ctx.protected_args + ctx.args
    while ctx is not None and args_remaining:
      if isinstance(ctx.command, MultiCommand):
        cmd = ctx.command.get_command(ctx, args_remaining[0])
        if cmd is None:
            return None
        ctx = cmd.make_context(args_remaining[0], args_remaining[1:], parent=ctx, resilient_parsing=True)
        args_remaining = ctx.protected_args + ctx.args
      else:
        ctx = ctx.parent

    return ctx

def get_choices(cli, prog_name, args, incomplete):
    ctx = resolve_ctx(cli, prog_name, args)
    if ctx is None:
        return

    choices = []
    incomplete_is_start_of_option = incomplete and not incomplete[:1].isalnum()
    if incomplete_is_start_of_option:
        for param in ctx.command.params:
            if not isinstance(param, Option):
                continue
            choices.extend(param.opts)
            choices.extend(param.secondary_opts)
    elif isinstance(ctx.command, MultiCommand):
        choices.extend(ctx.command.list_commands(ctx))

    if not incomplete_is_start_of_option and ctx.parent is not None and isinstance(ctx.parent.command, MultiCommand) and ctx.parent.command.chain:
        # completion for chained commands
        remaining_comands = set(ctx.parent.command.list_commands(ctx.parent))-set(ctx.parent.protected_args)
        choices.extend(remaining_comands)

    for item in choices:
        if item.startswith(incomplete):
            yield item


def do_complete(cli, prog_name):
    cwords = split_arg_string(os.environ['COMP_WORDS'])
    cword = int(os.environ['COMP_CWORD'])
    args = cwords[1:cword]
    try:
        incomplete = cwords[cword]
    except IndexError:
        incomplete = ''

    for item in get_choices(cli, prog_name, args, incomplete):
        echo(item)

    return True


def bashcomplete(cli, prog_name, complete_var, complete_instr):
    if complete_instr == 'source':
        echo(get_completion_script(prog_name, complete_var))
        return True
    elif complete_instr == 'complete':
        return do_complete(cli, prog_name)
    return False
