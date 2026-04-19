from __future__ import annotations

import inspect
import typing as t
from functools import update_wrapper
from gettext import gettext as _

from .core import Command
from .core import Context
from .core import Group
from .core import Option
from .core import Parameter
from .core import ParameterSource
from .core import UNSET
from .decorators import _param_memo
from .exceptions import Abort
from .exceptions import ClickException
from .termui import confirm
from .termui import prompt
from .termui import style
from .utils import echo

if t.TYPE_CHECKING:
    import typing_extensions as te

    P = te.ParamSpec("P")

R = t.TypeVar("R")
T = t.TypeVar("T")
_AnyCallable = t.Callable[..., t.Any]
FC = t.TypeVar("FC", bound="_AnyCallable | Command")


class InteractiveOption(Option):
    """
    An extension of Option that supports conditional prompting and
    additional interactive features.

    :param interactive: Whether this option should be prompted interactively.
        If set to True, the option will be prompted even if a default is set.
    :param interactive_when: A callable that determines if this option should
        be prompted interactively. It receives the current context and returns
        a boolean.
    :param interactive_after: The name of another parameter. This option will
        only be prompted if the specified parameter has a certain value.
    :param interactive_condition: A callable that receives the values of
        previously processed parameters and returns True if this option
        should be prompted.
    :param interactive_help: Additional help text to show during interactive
        prompting.
    """

    def __init__(
        self,
        param_decls: t.Sequence[str] | None = None,
        interactive: bool = False,
        interactive_when: t.Callable[[Context], bool] | None = None,
        interactive_after: str | None = None,
        interactive_condition: t.Callable[[dict[str, t.Any]], bool] | None = None,
        interactive_help: str | None = None,
        **attrs: t.Any,
    ) -> None:
        super().__init__(param_decls, **attrs)
        self.interactive = interactive
        self.interactive_when = interactive_when
        self.interactive_after = interactive_after
        self.interactive_condition = interactive_condition
        self.interactive_help = interactive_help

    def should_interactive_prompt(self, ctx: Context, params: dict[str, t.Any]) -> bool:
        """
        Determine if this option should be prompted interactively.
        """
        if not self.interactive and self.prompt is None:
            return False

        if self.interactive_when is not None:
            if not self.interactive_when(ctx):
                return False

        if self.interactive_after is not None:
            if self.interactive_after not in params:
                return False

        if self.interactive_condition is not None:
            if not self.interactive_condition(params):
                return False

        return True

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict.update(
            interactive=self.interactive,
            interactive_help=self.interactive_help,
        )
        return info_dict


class InteractiveCommand(Command):
    """
    A Command that supports interactive prompting for all parameters.

    :param interactive: Whether to enable interactive mode by default.
    :param interactive_all: Whether to prompt for all parameters interactively,
        even those without prompt=True.
    :param interactive_skip: List of parameter names to skip in interactive mode.
    """

    def __init__(
        self,
        name: str | None = None,
        interactive: bool = False,
        interactive_all: bool = False,
        interactive_skip: list[str] | None = None,
        **attrs: t.Any,
    ) -> None:
        super().__init__(name, **attrs)
        self.interactive = interactive
        self.interactive_all = interactive_all
        self.interactive_skip = interactive_skip or []

    def invoke(self, ctx: Context) -> t.Any:
        if self.interactive or ctx.params.get("_interactive", False):
            self._run_interactive_mode(ctx)

        return super().invoke(ctx)

    def _run_interactive_mode(self, ctx: Context) -> None:
        """
        Run the command in interactive mode, prompting for parameters.
        """
        echo(style(_("=== Interactive Mode ==="), fg="cyan", bold=True))
        echo()

        params = ctx.params.copy()
        processed_params: dict[str, t.Any] = {}

        for param in self.get_params(ctx):
            if param.name in self.interactive_skip:
                continue

            if param.name in params and params[param.name] is not None:
                if not self.interactive_all:
                    processed_params[param.name] = params[param.name]
                    continue

            if isinstance(param, InteractiveOption):
                if not param.should_interactive_prompt(ctx, processed_params):
                    continue

                if param.interactive_help:
                    echo(style(f"ℹ {param.interactive_help}", fg="yellow"))

                value = self._prompt_for_param(ctx, param)
                processed_params[param.name] = value
                ctx.params[param.name] = value
                ctx.set_parameter_source(param.name, ParameterSource.PROMPT)

            elif isinstance(param, Option):
                if param.prompt is not None or self.interactive_all:
                    value = self._prompt_for_param(ctx, param)
                    processed_params[param.name] = value
                    ctx.params[param.name] = value
                    ctx.set_parameter_source(param.name, ParameterSource.PROMPT)
                else:
                    if param.name in params:
                        processed_params[param.name] = params[param.name]

            elif param.name in params:
                processed_params[param.name] = params[param.name]

        echo()
        echo(style(_("=== Summary ==="), fg="cyan", bold=True))
        for name, value in processed_params.items():
            echo(f"  {name}: {value}")
        echo()

    def _prompt_for_param(self, ctx: Context, param: Parameter) -> t.Any:
        """
        Prompt the user for a parameter value.
        """
        if isinstance(param, Option):
            if param.prompt is not None:
                return param.prompt_for_value(ctx)
            else:
                prompt_text = param.name.replace("_", " ").capitalize() if param.name else "Value"

                if param.is_flag and param.is_bool_flag:
                    default = param.get_default(ctx)
                    if default is UNSET:
                        default = None
                    else:
                        default = bool(default)
                    return confirm(prompt_text, default=default)
                else:
                    default = param.get_default(ctx)
                    if default is UNSET:
                        default = None

                    return prompt(
                        prompt_text,
                        default=default,
                        type=param.type,
                        show_choices=getattr(param, "show_choices", True),
                    )

        return None


class InteractiveGroup(Group):
    """
    A Group that supports interactive mode for subcommands.

    :param interactive: Whether to enable interactive mode by default.
    :param interactive_menu: Whether to show an interactive menu for selecting
        subcommands when none is specified.
    """

    def __init__(
        self,
        name: str | None = None,
        interactive: bool = False,
        interactive_menu: bool = True,
        **attrs: t.Any,
    ) -> None:
        super().__init__(name, **attrs)
        self.interactive = interactive
        self.interactive_menu = interactive_menu

    def invoke(self, ctx: Context) -> t.Any:
        if self.interactive or ctx.params.get("_interactive", False):
            if not ctx.invoked_subcommand and self.interactive_menu:
                ctx.invoked_subcommand = self._show_interactive_menu(ctx)

        return super().invoke(ctx)

    def _show_interactive_menu(self, ctx: Context) -> str | None:
        """
        Show an interactive menu for selecting a subcommand.
        """
        echo(style(_("=== Available Commands ==="), fg="cyan", bold=True))

        commands = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd and not cmd.hidden:
                commands.append((name, cmd))

        if not commands:
            echo(_("No commands available."))
            return None

        for i, (name, cmd) in enumerate(commands, 1):
            help_text = cmd.get_short_help_str()
            echo(f"  {i}. {name:<20} - {help_text}")

        echo()

        while True:
            try:
                choice = prompt(
                    _("Enter command number or name"),
                    type=str,
                )

                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(commands):
                        return commands[idx][0]
                    else:
                        echo(style(_("Invalid selection. Please try again."), fg="red"))
                else:
                    for name, _ in commands:
                        if name.lower() == choice.lower():
                            return name
                    echo(style(_("Command not found. Please try again."), fg="red"))
            except (KeyboardInterrupt, EOFError):
                raise Abort()

    def command(
        self, *args: t.Any, **kwargs: t.Any
    ) -> t.Callable[[t.Callable[..., t.Any]], Command] | Command:
        if self.interactive and "interactive" not in kwargs:
            kwargs["interactive"] = True

        return super().command(*args, **kwargs)


def interactive_option(
    *param_decls: str,
    interactive: bool = True,
    interactive_when: t.Callable[[Context], bool] | None = None,
    interactive_after: str | None = None,
    interactive_condition: t.Callable[[dict[str, t.Any]], bool] | None = None,
    interactive_help: str | None = None,
    cls: type[InteractiveOption] | None = None,
    **attrs: t.Any,
) -> t.Callable[[FC], FC]:
    """
    Decorator to create an interactive option.

    This is similar to :func:`option`, but creates an :class:`InteractiveOption`
    that supports conditional prompting and additional interactive features.

    :param interactive: Whether this option should be prompted interactively.
    :param interactive_when: A callable that determines if this option should
        be prompted interactively.
    :param interactive_after: The name of another parameter. This option will
        only be prompted after the specified parameter.
    :param interactive_condition: A callable that receives the values of
        previously processed parameters and returns True if this option
        should be prompted.
    :param interactive_help: Additional help text to show during interactive
        prompting.
    :param cls: The option class to use. Defaults to :class:`InteractiveOption`.
    :param attrs: Other arguments passed to :class:`InteractiveOption`.

    Example::

        @click.command()
        @click.interactive_option('--name', prompt='Your name')
        @click.interactive_option('--age', type=int, interactive_help='Age in years')
        @click.interactive_option(
            '--city',
            interactive_after='name',
            interactive_condition=lambda params: params.get('age', 0) >= 18
        )
        def greet(name, age, city):
            click.echo(f'Hello {name}!')
    """
    if cls is None:
        cls = InteractiveOption

    def decorator(f: FC) -> FC:
        _param_memo(
            f,
            cls(
                param_decls,
                interactive=interactive,
                interactive_when=interactive_when,
                interactive_after=interactive_after,
                interactive_condition=interactive_condition,
                interactive_help=interactive_help,
                **attrs,
            ),
        )
        return f

    return decorator


def interactive_command(
    name: str | _AnyCallable | None = None,
    cls: type[InteractiveCommand] | None = None,
    interactive: bool = True,
    interactive_all: bool = False,
    interactive_skip: list[str] | None = None,
    **attrs: t.Any,
) -> InteractiveCommand | t.Callable[[_AnyCallable], InteractiveCommand]:
    """
    Decorator to create an interactive command.

    This is similar to :func:`command`, but creates an :class:`InteractiveCommand`
    that supports interactive prompting for parameters.

    :param name: The name of the command.
    :param cls: The command class to use. Defaults to :class:`InteractiveCommand`.
    :param interactive: Whether to enable interactive mode by default.
    :param interactive_all: Whether to prompt for all parameters interactively.
    :param interactive_skip: List of parameter names to skip in interactive mode.
    :param attrs: Other arguments passed to :class:`InteractiveCommand`.

    Example::

        @click.interactive_command()
        @click.option('--name', prompt='Your name')
        @click.option('--age', type=int, prompt='Your age')
        def greet(name, age):
            click.echo(f'Hello {name}, you are {age} years old!')
    """
    if cls is None:
        cls = InteractiveCommand

    func: t.Callable[[_AnyCallable], t.Any] | None = None

    if callable(name):
        func = name
        name = None

    def decorator(f: _AnyCallable) -> InteractiveCommand:
        from .decorators import command

        cmd = command(name, cls=cls, **attrs)(f)
        cmd.interactive = interactive
        cmd.interactive_all = interactive_all
        cmd.interactive_skip = interactive_skip or []
        return cmd

    if func is not None:
        return decorator(func)

    return decorator


def interactive_group(
    name: str | _AnyCallable | None = None,
    cls: type[InteractiveGroup] | None = None,
    interactive: bool = True,
    interactive_menu: bool = True,
    **attrs: t.Any,
) -> InteractiveGroup | t.Callable[[_AnyCallable], InteractiveGroup]:
    """
    Decorator to create an interactive group.

    This is similar to :func:`group`, but creates an :class:`InteractiveGroup`
    that supports interactive menus for subcommands.

    :param name: The name of the group.
    :param cls: The group class to use. Defaults to :class:`InteractiveGroup`.
    :param interactive: Whether to enable interactive mode by default.
    :param interactive_menu: Whether to show an interactive menu for selecting
        subcommands when none is specified.
    :param attrs: Other arguments passed to :class:`InteractiveGroup`.

    Example::

        @click.interactive_group()
        def cli():
            pass

        @cli.command()
        @click.option('--name', prompt='Your name')
        def greet(name):
            click.echo(f'Hello {name}!')
    """
    if cls is None:
        cls = InteractiveGroup

    func: t.Callable[[_AnyCallable], t.Any] | None = None

    if callable(name):
        func = name
        name = None

    def decorator(f: _AnyCallable) -> InteractiveGroup:
        from .decorators import group

        grp = group(name, cls=cls, **attrs)(f)
        grp.interactive = interactive
        grp.interactive_menu = interactive_menu
        return grp

    if func is not None:
        return decorator(func)

    return decorator


def with_interactive(f: t.Callable[te.Concatenate[bool, P], R]) -> t.Callable[P, R]:
    """
    Decorator that adds an --interactive flag to a command.

    When the --interactive flag is provided, the command will run in
    interactive mode, prompting for all parameters.

    Example::

        @click.command()
        @click.option('--name')
        @click.option('--age', type=int)
        @click.with_interactive
        def greet(interactive, name, age):
            click.echo(f'Hello {name}, you are {age} years old!')
    """

    def new_func(*args: P.args, **kwargs: P.kwargs) -> R:
        interactive = kwargs.pop("_interactive", False)
        return f(interactive, *args, **kwargs)

    return update_wrapper(new_func, f)
