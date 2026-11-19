from __future__ import annotations

import typing as t
from collections import defaultdict
from gettext import gettext as _
from gettext import ngettext

from ._base_utils import _split_opt
from ._utils import FLAG_NEEDS_VALUE
from ._utils import UNSET
from .exceptions import BadArgumentUsage
from .exceptions import BadOptionUsage
from .exceptions import NoSuchOption
from .exceptions import UsageError

if t.TYPE_CHECKING:
    from .core import Context
    from .core import Parameter


def _command_parse_args(
    ctx: Context, args: list[str], params: list[Parameter]
) -> list[str]:
    from .core import Argument
    from .core import iter_params_for_processing
    from .core import Option

    token_normalize_func = ctx.token_normalize_func

    def normalize(name: str) -> str:
        if token_normalize_func is None:
            return name

        prefix, name = _split_opt(name)
        return f"{prefix}{token_normalize_func(name)}"

    # Map each short and long option flag to their option objects, and collect the
    # order of positional arguments. The one and two character prefixes used by
    # options are collected to check if a token looks like an option.
    opt_prefixes: set[str] = {"-", "--"}
    short_opts: dict[str, Option] = {}
    long_opts: dict[str, Option] = {}
    # Normalized secondary names, for easier comparison during parsing.
    secondary_opts: set[str] = set()
    arg_params: list[Argument] = []
    # Normalized name to the option, declared spelling, and whether it's a
    # secondary name, to detect spellings that only collide after normalizing.
    claimed: dict[str, tuple[Option, str, bool]] = {}

    for param in params:
        if isinstance(param, Option):
            names = [(n, False) for n in param.opts]

            if param.is_bool_flag and param.secondary_opts:
                names.extend((n, True) for n in param.secondary_opts)
                secondary_opts.update(normalize(n) for n in param.secondary_opts)

            for original, is_secondary in names:
                name = normalize(original)

                if name in claimed:
                    other, other_original, other_is_secondary = claimed[name]

                    # An identical spelling is a duplicate declaration, which
                    # get_params warns about, and the last one keeps winning.
                    if original != other_original and (
                        other is not param or other_is_secondary != is_secondary
                    ):
                        raise TypeError(
                            _(
                                "The option names {first!r} and {second!r} both"
                                " normalize to {name!r}. Give them names that"
                                " stay distinct after 'token_normalize_func'."
                            ).format(first=other_original, second=original, name=name)
                        )

                claimed[name] = (param, original, is_secondary)
                prefix, value = _split_opt(name)
                opt_prefixes.add(prefix[0])

                if len(prefix) == 1 and len(value) == 1:
                    # -a is a short opt
                    short_opts[name] = param
                else:
                    # --a is a long opt, -ab is a long opt with a short prefix
                    opt_prefixes.add(prefix)
                    long_opts[name] = param

        elif isinstance(param, Argument):
            arg_params.append(param)

    def looks_like_opt(token: str) -> bool:
        return len(token) > 1 and token[:1] in opt_prefixes

    def flag_value(opt: Option, name: str) -> t.Any:
        if opt.count:
            # Each occurrence records the running count, the last one is used.
            return len(values[opt.name]) + 1

        if opt.is_bool_flag and opt.secondary_opts:
            return name not in secondary_opts

        return opt.flag_activation_value

    # Map parameter names to collected values.
    values: defaultdict[str, list[t.Any]] = defaultdict(list)
    # Track what order parameters were seen.
    param_order: list[Parameter] = []
    # After mapping arguments to values, any extra values will still be here.
    rest: list[str] = []
    # Track what the parser should do with the current token.
    lf_any = 0
    lf_value_or_opt = 1
    lf_value = 2
    looking_for = lf_any
    # Tracks the current option that needs a value.
    looking_opt: Option | None = None
    looking_opt_name: str | None = None
    # Treat tokens as a stack, with the first token at the top.
    tokens = list(reversed(args))

    try:
        while tokens:
            token = tokens.pop()

            if looking_for == lf_any:
                if token == "--":
                    # All tokens after -- are considered arguments.
                    rest.extend(reversed(tokens))
                    tokens.clear()
                elif looks_like_opt(token):
                    original_name, long_sep, value = token.partition("=")
                    name = normalize(original_name)

                    if name in long_opts:
                        # any prefix, matching long opt
                        opt = long_opts[name]
                        param_order.append(opt)
                        takes_value = not (opt.is_flag or opt.count)

                        if long_sep:
                            # key=value, only valid if the option takes a value
                            if not takes_value:
                                message = _(
                                    "Option {name!r} does not take a value."
                                ).format(name=original_name)
                                raise BadOptionUsage(original_name, message, ctx=ctx)

                            tokens.append(value)
                            looking_opt = opt
                            looking_opt_name = original_name
                            looking_for = lf_value
                        elif not takes_value:
                            # no attached value, and no value needed
                            values[opt.name].append(flag_value(opt, name))
                        else:
                            # no attached value, and a value may be needed
                            looking_opt = opt
                            looking_opt_name = original_name

                            if opt._flag_needs_value:
                                looking_for = lf_value_or_opt
                            else:
                                looking_for = lf_value
                    elif token[:2] in opt_prefixes:
                        # long prefix, no matching long opt
                        if not ctx.ignore_unknown_options:
                            raise NoSuchOption(
                                original_name, possibilities=long_opts, ctx=ctx
                            )

                        rest.append(token)
                    else:
                        # short prefix, try short opts
                        prefix = token[0]
                        chars = token[1:]
                        unmatched = []

                        for i, c in enumerate(chars, 1):
                            original_name = f"{prefix}{c}"
                            name = normalize(original_name)

                            if name not in short_opts:
                                if not ctx.ignore_unknown_options:
                                    raise NoSuchOption(name, ctx=ctx)

                                unmatched.append(c)
                                continue

                            opt = short_opts[name]
                            param_order.append(opt)

                            if opt.is_flag or opt.count:
                                # Record the flag, then continue trying short opts.
                                values[opt.name].append(flag_value(opt, name))
                                continue

                            # Not a flag, stop trying short options and begin
                            # looking for values.
                            looking_opt = opt
                            looking_opt_name = original_name
                            value = chars[i:]

                            if value:
                                # Use any remaining chars as a value.
                                tokens.append(value)
                                looking_for = lf_value
                            elif opt._flag_needs_value:
                                looking_for = lf_value_or_opt
                            else:
                                looking_for = lf_value

                            break

                        if unmatched:
                            # If unknown options are allowed, add any unused chars
                            # back as a single name with the same prefix.
                            rest.append(f"{prefix}{''.join(unmatched)}")
                else:
                    # an argument
                    rest.append(token)

                    if not ctx.allow_interspersed_args:
                        # If interspersed isn't allowed, all remaining
                        # tokens are considered arguments.
                        rest.extend(reversed(tokens))
                        tokens.clear()
            elif looking_for == lf_value_or_opt:
                # The current opt optionally takes a value. Look at the
                # token then put it back.
                assert looking_opt is not None
                tokens.append(token)

                if (looking_opt.nargs == 1 and looks_like_opt(token)) or len(
                    tokens
                ) < looking_opt.nargs:
                    # Next token is an opt, or there aren't enough tokens left.
                    # Mark the current opt as needing a value, handled during
                    # processing.
                    values[looking_opt.name].append(FLAG_NEEDS_VALUE)
                    looking_opt = looking_opt_name = None
                    looking_for = lf_any
                else:
                    # Next token will be used as a value.
                    looking_for = lf_value
            elif looking_for == lf_value:
                # The current opt requires at least one value.
                assert looking_opt is not None and looking_opt_name is not None

                if looking_opt.nargs == 1:
                    # Exactly one value required
                    values[looking_opt.name].append(token)
                else:
                    # More than one value required
                    need_n = looking_opt.nargs - 1

                    if len(tokens) < need_n:
                        message = ngettext(
                            "Option {name!r} requires {nargs} values but 1 was given.",
                            "Option {name!r} requires {nargs} values"
                            " but {len} were given.",
                            len(tokens) + 1,
                        ).format(
                            name=looking_opt_name,
                            nargs=looking_opt.nargs,
                            len=len(tokens) + 1,
                        )
                        raise BadOptionUsage(looking_opt_name, message, ctx=ctx)

                    values[looking_opt.name].append(
                        (token, *reversed(tokens[-need_n:]))
                    )
                    del tokens[-need_n:]

                looking_opt = looking_opt_name = None
                looking_for = lf_any

        if looking_for == lf_value_or_opt:
            # No more tokens, mark the current opt to get a value later.
            assert looking_opt is not None
            values[looking_opt.name].append(FLAG_NEEDS_VALUE)
        elif looking_for == lf_value:
            # No more tokens, but the current opt still required a value.
            assert looking_opt is not None and looking_opt_name is not None
            message = ngettext(
                "Option {name!r} requires a value.",
                "Option {name!r} requires {nargs} values.",
                looking_opt.nargs,
            ).format(name=looking_opt_name, nargs=looking_opt.nargs)
            raise BadOptionUsage(looking_opt_name, message, ctx=ctx)

        # Treat args as a stack, with the first at the top.
        arg_params.reverse()

        while arg_params:
            arg = arg_params.pop()
            param_order.append(arg)

            # Missing values aren't recorded, so the value can come from an env
            # var or default, or be reported as missing during processing.
            if arg.nargs == -1:
                need_n = sum(p.nargs for p in arg_params if p.nargs > 0)

                if need_n:
                    buffer = rest[:-need_n]
                    rest = rest[-need_n:]
                else:
                    buffer = rest
                    rest = []

                if buffer:
                    values[arg.name].append(tuple(buffer))
            elif arg.nargs == 1:
                if rest:
                    values[arg.name].append(rest.pop(0))
            elif len(rest) >= arg.nargs:
                values[arg.name].append(tuple(rest[: arg.nargs]))
                rest = rest[arg.nargs :]
            elif rest:
                message = ngettext(
                    "Argument {name!r} requires {nargs} values but 1 was given.",
                    "Argument {name!r} requires {nargs} values but {len} were given.",
                    len(rest),
                ).format(name=arg.make_metavar(ctx), nargs=arg.nargs, len=len(rest))
                raise BadArgumentUsage(message, ctx=ctx)
    except UsageError:
        if not ctx.resilient_parsing:
            raise

    args = rest

    for param in iter_params_for_processing(param_order, params):
        args = param.handle_parse_result(ctx, values, args)[1]

    # We now have all parameters' values into `ctx.params`, but the data may contain
    # the `UNSET` sentinel.
    # Convert `UNSET` to `None` to ensure that the user doesn't see `UNSET`.
    #
    # Waiting until after the initial parse to convert allows us to treat `UNSET`
    # more like a missing value when multiple params use the same name.
    for name, value in ctx.params.items():
        if value is UNSET:
            ctx.params[name] = None

    if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
        message = ngettext(
            "Got unexpected extra argument ({args})",
            "Got unexpected extra arguments ({args})",
            len(args),
        ).format(args=" ".join(args))
        raise BadArgumentUsage(message, ctx=ctx)

    ctx.args = args
    ctx._opt_prefixes.update(opt_prefixes)
    return args
