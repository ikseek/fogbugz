"""Test basic fogbugz API operations."""
import httpretty
import pytest

from fogbugz import FogBugzLogonError


def test_logon(fogbugz, fogbugz_api_uri):
    """Test successful login."""
    httpretty.register_uri(httpretty.POST, fogbugz_api_uri, body='<response><token>24dsg34lok43un23</token></response>')
    fogbugz.logon('user', 'password')
    assert fogbugz._token == '24dsg34lok43un23'


def test_logon_failed(fogbugz, fogbugz_api_uri):
    """Test unsuccessful login."""
    httpretty.register_uri(
        httpretty.POST, fogbugz_api_uri, body='<response><error code="1">Error Message To Show User</error></response>')
    with pytest.raises(FogBugzLogonError):
        fogbugz.logon('user', 'password')
