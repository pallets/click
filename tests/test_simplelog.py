import re
import sys
import click
import logging


# Set up logger for tests


class ClickStream(object):

    """ Logger Stream handler, which uses click.echo - Thanks to @unittaker
    """

    def write(self, string):
        click.echo(string, file=sys.stdout, nl=False)

stdout_handler = logging.StreamHandler(ClickStream())
formatter = logging.Formatter()
stdout_handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.handlers = [stdout_handler]


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

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\nCRITICAL\nERROR\n"


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

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\nCRITICAL\nERROR\n"


def tool_run_cli(runner, simplelog_opts={}, cli_args=None):

    @click.command()
    @click.simplelog(**simplelog_opts)
    def cli(*args, **kwargs):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    return runner.invoke(cli, cli_args)


def test_simplelog_defaults(runner):

    result = tool_run_cli(runner)

    assert result.output == "CRITICAL\nERROR\n"


def test_simplelog_defaults_help(runner):

    result = tool_run_cli(runner, cli_args=["--help"])

    for output in (
        "-q, --quiet *Enable quiet mode",
        "-v, --verbose *Enable verbose logging",
        "-d, --debug *Enable debugging"
    ):

        assert re.search(output, result.output) is not None


def test_simplelog_quiet(runner):

    result = tool_run_cli(runner, cli_args=["--quiet"])

    assert result.output == "CRITICAL\n"


def test_simplelog_verbose(runner):

    result = tool_run_cli(runner, cli_args=["--verbose"])

    assert result.output == "CRITICAL\nERROR\nINFO\n"


def test_simplelog_debug(runner):

    result = tool_run_cli(runner, cli_args=["--debug"])

    assert result.output == "CRITICAL\nERROR\nINFO\nDEBUG\n"


def test_simplelog_vvvflavor_quiet(runner):

    result = tool_run_cli(runner, simplelog_opts={"flavor": "vvv"})

    assert result.output == "CRITICAL\n"


def test_simplelog_vvvflavor_defaults(runner):

    result = tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-v"]
    )

    assert result.output == "CRITICAL\nERROR\n"


def test_simplelog_vvvflavor_verbose(runner):

    result = tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-vv"]
    )

    assert result.output == "CRITICAL\nERROR\nINFO\n"


def test_simplelog_vvvflavor_debug(runner):

    result = tool_run_cli(
        runner,
        simplelog_opts={"flavor": "vvv"},
        cli_args=["-vvv"]
    )

    assert result.output == "CRITICAL\nERROR\nINFO\nDEBUG\n"


def test_simplelog_invalidflavor(runner):

    try:

        result = tool_run_cli(
            runner,
            simplelog_opts={"flavor": "INVALID"},
        )

    except Exception as e:

        return

    assert result.exception
