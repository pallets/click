import logging

import click
from click.testing import CliRunner


# Minimized version of:
# https://github.com/pallets/click/issues/824#issuecomment-3027263262
#
# Test needs to be run as "pytest --log-cli-level 30 tests/test_testing_logging.py"
# to test the intended functionality.
def test_runner_logger():
    logger = logging.getLogger(__name__)

    @click.command()
    @click.option("--name", prompt="Your name", help="The person to greet.")
    def hello(name):
        logger.warning("Greeting user now...")
        click.echo(f"Hello, {name}!")

    runner = CliRunner()
    result = runner.invoke(hello, input="Peter")
    assert result.exit_code == 0
    # FIXME: second half of the output is missing with --log-cli-level 30.
    assert result.output in ("Your name: Peter\n", "Your name: Peter\nHello, Peter!\n")
