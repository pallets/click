"""
Web API for Interactive Click Commands

This module provides a Flask-based API that allows executing Click commands
interactively through HTTP requests. It captures prompts and returns them
to the client for user input.
"""

from __future__ import annotations

import io
import sys
import typing as t
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from flask import Flask, jsonify, request
from flask_cors import CORS

import click
from click._termui_impl import ProgressBar
from click.core import Command, Context, Group, Option, Parameter
from click.termui import confirm, prompt


class InteractivePromptCapture:
    """
    A class that captures prompts and allows providing answers programmatically.
    """

    def __init__(self) -> None:
        self.prompts: list[dict[str, t.Any]] = []
        self.answers: list[t.Any] = []
        self.current_prompt_index = 0

    def capture_prompt(
        self,
        text: str,
        default: t.Any | None = None,
        hide_input: bool = False,
        type: t.Any | None = None,
        **kwargs: t.Any,
    ) -> t.Any:
        """
        Capture a prompt and return the answer if available,
        otherwise raise a special exception to indicate waiting for input.
        """
        prompt_info = {
            "type": "prompt",
            "text": text,
            "default": default,
            "hide_input": hide_input,
            "type": str(type) if type else None,
            "choices": getattr(type, "choices", None) if hasattr(type, "choices") else None,
        }
        self.prompts.append(prompt_info)

        if self.current_prompt_index < len(self.answers):
            answer = self.answers[self.current_prompt_index]
            self.current_prompt_index += 1
            return answer
        else:
            raise PromptWaitingException(prompt_info)

    def capture_confirm(
        self,
        text: str,
        default: bool | None = False,
        **kwargs: t.Any,
    ) -> bool:
        """
        Capture a confirmation prompt.
        """
        prompt_info = {
            "type": "confirm",
            "text": text,
            "default": default,
        }
        self.prompts.append(prompt_info)

        if self.current_prompt_index < len(self.answers):
            answer = self.answers[self.current_prompt_index]
            self.current_prompt_index += 1
            return bool(answer)
        else:
            raise PromptWaitingException(prompt_info)

    def set_answers(self, answers: list[t.Any]) -> None:
        """Set the answers for the prompts."""
        self.answers = answers
        self.current_prompt_index = 0

    def reset(self) -> None:
        """Reset the capture state."""
        self.prompts = []
        self.answers = []
        self.current_prompt_index = 0


class PromptWaitingException(Exception):
    """Exception raised when waiting for user input for a prompt."""

    def __init__(self, prompt_info: dict[str, t.Any]) -> None:
        self.prompt_info = prompt_info
        super().__init__("Waiting for user input")


app = Flask(__name__)
CORS(app)

prompt_capture = InteractivePromptCapture()


def get_command_info(cmd: Command, ctx: Context | None = None) -> dict[str, t.Any]:
    """
    Get information about a command, including its parameters.
    """
    if ctx is None:
        ctx = Context(cmd)

    info = {
        "name": cmd.name,
        "help": cmd.help,
        "short_help": cmd.get_short_help_str(),
        "params": [],
        "is_group": isinstance(cmd, Group),
    }

    for param in cmd.get_params(ctx):
        param_info = {
            "name": param.name,
            "type": param.param_type_name,
            "required": param.required,
            "help": getattr(param, "help", None),
            "default": param.default if param.default is not click.UNSET else None,
            "has_prompt": getattr(param, "prompt", None) is not None,
            "prompt": getattr(param, "prompt", None),
            "is_flag": getattr(param, "is_flag", False),
            "is_bool_flag": getattr(param, "is_bool_flag", False),
            "hide_input": getattr(param, "hide_input", False),
            "type_info": param.type.to_info_dict() if hasattr(param.type, "to_info_dict") else {},
        }

        if hasattr(param.type, "choices"):
            param_info["choices"] = list(param.type.choices)

        info["params"].append(param_info)

    if isinstance(cmd, Group):
        info["commands"] = {}
        for name in cmd.list_commands(ctx):
            sub_cmd = cmd.get_command(ctx, name)
            if sub_cmd and not sub_cmd.hidden:
                info["commands"][name] = get_command_info(sub_cmd, ctx)

    return info


def execute_command_with_capture(
    cmd: Command,
    args: list[str],
    answers: list[t.Any] | None = None,
) -> dict[str, t.Any]:
    """
    Execute a command with prompt capture.
    """
    original_prompt = click.termui.prompt
    original_confirm = click.termui.confirm

    prompt_capture.reset()
    if answers:
        prompt_capture.set_answers(answers)

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        click.termui.prompt = prompt_capture.capture_prompt
        click.termui.confirm = prompt_capture.capture_confirm

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                result = cmd.main(args, standalone_mode=False)
                return {
                    "status": "completed",
                    "result": result,
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue(),
                    "prompts": prompt_capture.prompts,
                }
            except PromptWaitingException as e:
                return {
                    "status": "waiting_for_input",
                    "prompt": e.prompt_info,
                    "prompts": prompt_capture.prompts,
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue(),
                }
            except SystemExit as e:
                return {
                    "status": "completed",
                    "exit_code": e.code,
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue(),
                    "prompts": prompt_capture.prompts,
                }
            except click.ClickException as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue(),
                    "prompts": prompt_capture.prompts,
                }
    finally:
        click.termui.prompt = original_prompt
        click.termui.confirm = original_confirm


@app.route("/api/commands", methods=["GET"])
def list_commands() -> t.Any:
    """
    List all available commands.
    """
    from examples.interactive.interactive_demo import cli

    info = get_command_info(cli)
    return jsonify({"commands": info})


@app.route("/api/commands/<path:command_path>", methods=["GET"])
def get_command(command_path: str) -> t.Any:
    """
    Get information about a specific command.
    """
    from examples.interactive.interactive_demo import cli

    parts = command_path.split("/")
    cmd: Command | None = cli

    for part in parts:
        if isinstance(cmd, Group):
            cmd = cmd.get_command(Context(cmd), part)
        else:
            cmd = None
        if cmd is None:
            return jsonify({"error": f"Command not found: {command_path}"}), 404

    info = get_command_info(cmd)
    return jsonify({"command": info})


@app.route("/api/execute", methods=["POST"])
def execute_command() -> t.Any:
    """
    Execute a command with optional answers for prompts.

    Request body:
    {
        "command": ["command", "subcommand"],
        "args": ["--option", "value"],
        "answers": ["answer1", "answer2", ...]
    }
    """
    from examples.interactive.interactive_demo import cli

    data = request.get_json() or {}

    command_parts = data.get("command", [])
    args = data.get("args", [])
    answers = data.get("answers")

    full_args = command_parts + args

    result = execute_command_with_capture(cli, full_args, answers)
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health_check() -> t.Any:
    """
    Health check endpoint.
    """
    return jsonify({"status": "ok", "message": "Interactive Click API is running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
