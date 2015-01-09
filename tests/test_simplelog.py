import StringIO
import re
import click
import logging


log_stream = StringIO.StringIO()
logging.basicConfig(stream=log_stream)


def test_simplelog_defaults(runner):

    @click.command()
    @click.simplelog()
    def cli(verbose, quiet, debug):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli)

    assert log_stream.getvalue() == "CRITICAL:root:CRITICAL\nERROR:root:ERROR\n"


def test_simplelog_defaults_option(runner):

    @click.command()
    @click.simplelog()
    @click.option("--test")
    def cli(verbose, quiet, debug, test):

        print test

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\n"
    assert log_stream.getvalue() == "CRITICAL:root:CRITICAL\nERROR:root:ERROR\n"


def test_simplelog_defaults_option_remove_args(runner):

    @click.command()
    @click.simplelog(remove_args=True)
    @click.option("--test")
    def cli(test):

        print test

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli, ["--test=test"])

    assert result.output == "test\n"
    assert log_stream.getvalue() == "CRITICAL:root:CRITICAL\nERROR:root:ERROR\n"


def test_simplelog_defaults_help(runner):

    @click.command()
    @click.simplelog()
    @click.option("--test")
    def cli(verbose, quiet, debug):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    result = runner.invoke(cli, ["--help"])

    for output in (
        "-q, --quiet *Enable quiet mode",
        "-v, --verbose *Enable verbose logging",
        "-d, --debug *Enable debugging"
    ):

        assert re.search(output, result.output) is not None


def test_simplelog_quiet(runner):

    @click.command()
    @click.simplelog()
    def cli(verbose, quiet, debug):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli, ["--quiet"])

    assert log_stream.getvalue() == "CRITICAL:root:CRITICAL\n"


def test_simplelog_verbose(runner):

    @click.command()
    @click.simplelog()
    def cli(verbose, quiet, debug):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli, ["-v"])

    assert log_stream.getvalue() == \
        "CRITICAL:root:CRITICAL\nERROR:root:ERROR\nINFO:root:INFO\n"


def test_simplelog_debug(runner):

    @click.command()
    @click.simplelog()
    def cli(verbose, quiet, debug):

        logging.critical("CRITICAL")
        logging.error("ERROR")
        logging.info("INFO")
        logging.debug("DEBUG")

    log_stream.truncate(0)

    result = runner.invoke(cli, ["-d"])

    assert log_stream.getvalue() == \
        "CRITICAL:root:CRITICAL\nERROR:root:ERROR\n" \
        "INFO:root:INFO\nDEBUG:root:DEBUG\n"
