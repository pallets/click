import collections
import copy
import os
import re

from .utils import echo
from .parser import split_arg_string
from .core import MultiCommand, Option, Argument
from .types import Choice

WORDBREAK = '='

COMPLETION_SCRIPT = '''
%(complete_func)s() {
    local IFS=$'\n'
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
    """
    Parse into a hierarchy of contexts. Contexts are connected through the parent variable.
    :param cli: command definition
    :param prog_name: the program that is running
    :param args: full list of args
    :return: the final context/command parsed
    """
    ctx = cli.make_context(prog_name, args, resilient_parsing=True)
    args_remaining = ctx.protected_args + ctx.args
    while ctx is not None and args_remaining:
        if isinstance(ctx.command, MultiCommand):
            cmd = ctx.command.get_command(ctx, args_remaining[0])
            if cmd is None:
                return None
            ctx = cmd.make_context(
                args_remaining[0], args_remaining[1:], parent=ctx, resilient_parsing=True)
            args_remaining = ctx.protected_args + ctx.args
        elif ctx.parent is not None:
            ctx = ctx.parent
        else:
            break

    return ctx


def start_of_option(param_str):
    """
    :param param_str: param_str to check
    :return: whether or not this is the start of an option declaration (i.e. starts "-" or "--")
    """
    return param_str and param_str[:1] == '-'


def is_incomplete_option(all_args, cmd_param):
    """
    :param all_args: the full original list of args supplied
    :param cmd_param: the current command paramter
    :return: whether or not the last option declaration (i.e. starts "-" or "--") is incomplete and
    corresponds to this cmd_param. In other words whether this cmd_param option can still accept
    values
    """
    if not isinstance(cmd_param, Option):
        return False
    if cmd_param.is_flag:
        return False
    last_option = None
    for index, arg_str in enumerate(reversed([arg for arg in all_args if arg != WORDBREAK])):
        if index + 1 > cmd_param.nargs:
            break
        if start_of_option(arg_str):
            last_option = arg_str

    return True if last_option and last_option in cmd_param.opts else False


def is_incomplete_argument(current_params, cmd_param):
    """
    :param current_params: the current params and values for this argument as already entered
    :param cmd_param: the current command parameter
    :return: whether or not the last argument is incomplete and corresponds to this cmd_param. In
    other words whether or not the this cmd_param argument can still accept values
    """
    if not isinstance(cmd_param, Argument):
        return False
    current_param_values = current_params[cmd_param.name]
    if current_param_values is None:
        return True
    if cmd_param.nargs == -1:
        return True
    if isinstance(current_param_values, collections.Iterable) \
            and cmd_param.nargs > 1 and len(current_param_values) < cmd_param.nargs:
        return True
    return False


def get_user_autocompletions(ctx, args, incomplete, cmd_param):
    """
    :param ctx: context associated with the parsed command
    :param args: full list of args
    :param incomplete: the incomplete text to autocomplete
    :param cmd_param: command definition
    :return: all the possible user-specified completions for the param
    """
    if isinstance(cmd_param.type, Choice):
        return [c for c in cmd_param.type.choices if c.startswith(incomplete)]
    elif cmd_param.autocompletion is not None:
        return cmd_param.autocompletion(ctx=ctx,
                                        args=args,
                                        incomplete=incomplete)
    else:
        return []


def add_subcommand_completions(ctx, incomplete, completions_out):
    # Add subcommand completions.
    if isinstance(ctx.command, MultiCommand):
        completions_out.extend(
            [c for c in ctx.command.list_commands(ctx) if c.startswith(incomplete)])

    # Walk up the context list and add any other completion possibilities from chained commands
    while ctx.parent is not None:
        ctx = ctx.parent
        if isinstance(ctx.command, MultiCommand) and ctx.command.chain:
            remaining_commands = sorted(
                set(ctx.command.list_commands(ctx)) - set(ctx.protected_args))
            completions_out.extend(
                [c for c in remaining_commands if c.startswith(incomplete)])


def get_choices(cli, prog_name, args, incomplete):
    """
    :param cli: command definition
    :param prog_name: the program that is running
    :param args: full list of args
    :param incomplete: the incomplete text to autocomplete
    :return: all the possible completions for the incomplete
    """
    all_args = copy.deepcopy(args)

    ctx = resolve_ctx(cli, prog_name, args)
    if ctx is None:
        return []

    # In newer versions of bash long opts with '='s are partitioned, but it's easier to parse
    # without the '='
    if start_of_option(incomplete) and WORDBREAK in incomplete:
        partition_incomplete = incomplete.partition(WORDBREAK)
        all_args.append(partition_incomplete[0])
        incomplete = partition_incomplete[2]
    elif incomplete == WORDBREAK:
        incomplete = ''

    completions = []
    if start_of_option(incomplete):
        # completions for partial options
        for param in ctx.command.params:
            if isinstance(param, Option):
                param_opts = [param_opt for param_opt in param.opts +
                              param.secondary_opts if param_opt not in all_args or param.multiple]
                completions.extend(
                    [c for c in param_opts if c.startswith(incomplete)])
        return completions
    # completion for option values from user supplied values
    for param in ctx.command.params:
        if is_incomplete_option(all_args, param):
            return get_user_autocompletions(ctx, all_args, incomplete, param)
    # completion for argument values from user supplied values
    for param in ctx.command.params:
        if is_incomplete_argument(ctx.params, param):
            completions.extend(get_user_autocompletions(
                ctx, all_args, incomplete, param))
            # Stop looking for other completions only if this argument is required.
            if param.required:
                return completions
            break

    add_subcommand_completions(ctx, incomplete, completions)
    return completions


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
