import os
import re
from .utils import echo
from .parser import split_arg_string
from .core import MultiCommand, Option


COMPLETION_SCRIPT = '''
complete --command %(script_names)s --arguments "(env %(autocomplete_var)s=complete-fish COMMANDLINE=(commandline -cp) %(script_names)s)" -f
'''

_invalid_ident_char_re = re.compile(r'[^a-zA-Z0-9_]')


def get_completion_script(prog_name, complete_var):
    cf_name = _invalid_ident_char_re.sub('', prog_name.replace('-', '_'))
    return (COMPLETION_SCRIPT % {
        'script_names': prog_name,
        'autocomplete_var': complete_var,
    }).strip() + ';'


def resolve_ctx(cli, prog_name, args):
    ctx = cli.make_context(prog_name, args, resilient_parsing=True)
    while ctx.args + ctx.protected_args and isinstance(ctx.command, MultiCommand):
        a = ctx.args + ctx.protected_args
        cmd = ctx.command.get_command(ctx, a[0])
        if cmd is None:
            return None
        ctx = cmd.make_context(a[0], a[1:], parent=ctx, resilient_parsing=True)
    return ctx


def get_choices(cli, prog_name, args, incomplete):
    ctx = resolve_ctx(cli, prog_name, args)
    if ctx is None:
        return

    choices = []
    if incomplete and not incomplete[:1].isalnum():
        for param in ctx.command.params:
            if not isinstance(param, Option):
                continue
            for opt in param.opts:
              choices.append((opt, param.help))
            for opt in param.secondary_opts:
              # don't put the doc so fish won't group the primary and
              # and secondary options
              choices.append((opt, None))
    elif isinstance(ctx.command, MultiCommand):
        for name in ctx.command.list_commands(ctx):
            cmd = ctx.command.get_command(ctx, name)
            choices.append((cmd.name, cmd.short_help))

    for item, help in choices:
        if item.startswith(incomplete):
            yield (item, help)


def do_complete(cli, prog_name):
    commandline = os.environ['COMMANDLINE']
    args = split_arg_string(commandline)[1:]
    if args and not commandline.endswith(' '):
        incomplete = args[-1]
        args = args[:-1]
    else:
        incomplete = ''

    for item, help in get_choices(cli, prog_name, args, incomplete):
        if help:
            echo("%s\t%s" % (item, help))
        else:
            echo(item)

    return True


def fishcomplete(cli, prog_name, complete_var, complete_instr):
    if complete_instr == 'source-fish':
        echo(get_completion_script(prog_name, complete_var))
        return True
    elif complete_instr == 'complete-fish':
        return do_complete(cli, prog_name)
    return False
