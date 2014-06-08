from click.testing import CLIRunner

import pytest


@pytest.fixture(scope='function')
def runner(request):
    return CLIRunner()
