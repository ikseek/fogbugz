"""Tests configuration."""
import pytest

import httpretty

from fogbugz import FogBugz


@pytest.fixture
def fogbugz_uri():
    """test Fogbugz URI."""
    return 'http://fogbugz.example.com/'


@pytest.fixture
def fogbugz_api_uri(fogbugz_uri):
    """test Fogbugz API uri."""
    return fogbugz_uri + 'api.asp?'


@pytest.yield_fixture
def fogbugz(fogbugz_uri):
    """Test fogbugz instance."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, fogbugz_uri + 'api.xml',
        body="""<response>
<version>8</version>
<minversion>1</minversion>
<url>api.asp?</url>
</response>""")
    yield FogBugz(fogbugz_uri)
    httpretty.disable()
