import sys

import re
import click
import logging

log_stream = None


def tool_resetlog():

    global log_stream

    logging.basicConfig()

    root = logging.getLogger()

    for handler in root.handlers:

        root.removeHandler(handler)

    if sys.version < '3':

        import StringIO
        log_stream = StringIO.StringIO()

    else:

        import io
        log_stream = io.StringIO()

    handler = logging.StreamHandler(log_stream)

    root.addHandler(handler)


def test_simplelog_defaults_option(runner):

    @click.command()
    @click.simplelog()
    @click.option("--test")
    def cli(verbose, quiet, debug, test):

        print(test)

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    tool_resetlog()

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\n"
    assert log_stream.getvalue() == "CRITICAL\nERROR\n"


def test_simplelog_defaults_option_remove_args(runner):

    @click.command()
    @click.simplelog(remove_args=True)
    @click.option("--test")
    def cli(test):

        print(test)

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    tool_resetlog()

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\n"
    assert log_stream.getvalue() == "CRITICAL\nERROR\n"


def tool_run_cli(runner, simplelog_opts={}, cli_args=None):

    @click.command()
    @click.simplelog(**simplelog_opts)
    def cli(*args, **kwargs):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    tool_resetlog()

    return runner.invoke(cli, cli_args)


def test_simplelog_defaults(runner):

    tool_run_cli(runner)

    assert log_stream.getvalue() == "CRITICAL\nERROR\n"


def test_simplelog_defaults_help(runner):

    result = tool_run_cli(runner, cli_args=["--help"])

    for output in (
        "-q, --quiet *Enable quiet mode",
        "-v, --verbose *Enable verbose logging",
        "-d, --debug *Enable debugging"
    ):

        assert re.search(output, result.output) is not None


def test_simplelog_quiet(runner):

    tool_run_cli(runner, cli_args=["--quiet"])

    assert log_stream.getvalue() == "CRITICAL\n"


def test_simplelog_verbose(runner):

    tool_run_cli(runner, cli_args=["--verbose"])

    assert log_stream.getvalue() == "CRITICAL\nERROR\nINFO\n"


def test_simplelog_debug(runner):

    tool_run_cli(runner, cli_args=["--debug"])

    assert log_stream.getvalue() == "CRITICAL\nERROR\nINFO\nDEBUG\n"


def test_simplelog_vvvflavor_quiet(runner):

    tool_run_cli(runner, simplelog_opts={"flavor": "vvv"})

    assert log_stream.getvalue() == "CRITICAL\n"


def test_simplelog_vvvflavor_defaults(runner):

    tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-v"]
    )

    assert log_stream.getvalue() == "CRITICAL\nERROR\n"


def test_simplelog_vvvflavor_verbose(runner):

    tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-vv"]
    )

    assert log_stream.getvalue() == "CRITICAL\nERROR\nINFO\n"


def test_simplelog_vvvflavor_debug(runner):

    tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-vvv"]
    )

    assert log_stream.getvalue() == "CRITICAL\nERROR\nINFO\nDEBUG\n"


def test_simplelog_invalidflavor(runner):

    try:

        result = tool_run_cli(
            runner,
            simplelog_opts={"flavor": "INVALID"},
        )

    except Exception as e:

        return

    assert result.exception

