from click.testing import CliRunner

import pytest


@pytest.fixture(scope='function')
def runner(request):
    return CliRunner()
