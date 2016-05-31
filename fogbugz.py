from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
try:
    # For Python 3.0 and later
    from urllib.request import Request, build_opener
    from urllib.error import HTTPError, URLError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import HTTPError, URLError, Request, build_opener
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO
from email.generator import _make_boundary

from bs4 import BeautifulSoup, CData

DEBUG = False  # Set to True for debugging output.


class FogBugzAPIError(Exception):
    pass


class FogBugzLogonError(FogBugzAPIError):
    pass


class FogBugzConnectionError(FogBugzAPIError):
    pass


class FogBugz:

    def __init__(self, url, token=None, soup_features="html.parser"):
        self.__handlerCache = {}
        if not url.endswith('/'):
            url += '/'

        if token:
            self._token = token
        else:
            self._token = None
        self._soup_features = soup_features

        self._opener = build_opener()
        try:
            soup = BeautifulSoup(self._opener.open(url + 'api.xml'),
                                 features=self._soup_features)
        except (URLError, HTTPError) as e:
            raise FogBugzConnectionError(
                "Library could not connect to the FogBugz API.  "
                "Either this installation of FogBugz does not "
                "support the API, or the url, %s, is incorrect.\n\n"
                "Error: %s" % (url, e))
        self._url = url + soup.response.url.string
        self.currentFilter = None

    def logon(self, username, password):
        """
        Logs the user on to FogBugz.

        Returns None for a successful login.
        """
        if self._token:
            self.logoff()
        try:
            response = self.__makerequest(
                'logon', email=username, password=password)
        except FogBugzAPIError as e:
            raise FogBugzLogonError(e)
        self._token = response.token.string
        if type(self._token) == CData:
            self._token = self._token

    def logoff(self):
        """
        Logs off the current user.
        """
        self.__makerequest('logoff')
        self._token = None

    def token(self, token):
        """
        Set the token without actually logging on.  More secure.
        """
        self._token = token

    def __encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (key, value) elements for regular form fields.
        files is a sequence of (filename, filehandle) files to be uploaded
        returns (content_type, body)
        """
        BOUNDARY = _make_boundary()

        if len(files) > 0:
            fields['nFileCount'] = str(len(files))

        crlf = '\r\n'
        buf = StringIO()

        for k, v in list(fields.items()):
            if DEBUG:
                print(("field: %s: %s" % (repr(k), repr(v))))
            buf.write(crlf.join(
                ['--' + BOUNDARY,
                 'Content-disposition: form-data; name="%s"' % k,
                 '', str(v), '']))

        n = 0
        for f, h in list(files.items()):
            n += 1
            buf.write(crlf.join(
                ['--' + BOUNDARY,
                 'Content-disposition: form-data;'
                 ' name="File%d"; filename="%s"' % (n, f), '']))
            buf.write(
                crlf.join(['Content-type: application/octet-stream', '', '']))
            buf.write(h.read())
            buf.write(crlf)

        buf.write('--' + BOUNDARY + '--' + crlf)
        content_type = "multipart/form-data; boundary=%s" % BOUNDARY
        return content_type, buf.getvalue().encode('utf-8')

    def __makerequest(self, cmd, **kwargs):
        kwargs["cmd"] = cmd
        if self._token:
            kwargs["token"] = self._token

        fields = dict([k, v] for k, v in list(kwargs.items()))
        files = fields.get('Files', {})
        if 'Files' in fields:
            del fields['Files']

        content_type, body = self.__encode_multipart_formdata(fields, files)
        headers = {'Content-Type': content_type,
                   'Content-Length': str(len(body))}

        try:
            request = Request(self._url, body, headers)
            soup = BeautifulSoup(self._opener.open(request),
                                 features=self._soup_features)
        except URLError as e:
            raise FogBugzConnectionError(e)

        response = soup.response
        if response is None:
            raise FogBugzConnectionError("Unexpected FogBugz server response",
                                         soup)

        if response.error:
            raise FogBugzAPIError('Error Code %s: %s' % (
                response.error['code'], response.error.string,))
        return response

    def __getattr__(self, name):
        """
        Handle all FogBugz API calls.

        >>> fb.logon(email@example.com, password)
        >>> response = fb.search(q="assignedto:email")
        """

        # Let's leave the private stuff to Python
        if name.startswith("__"):
            raise AttributeError("No such attribute '%s'" % name)

        if name not in self.__handlerCache:
            def handler(**kwargs):
                return self.__makerequest(name, **kwargs)
            self.__handlerCache[name] = handler
        return self.__handlerCache[name]
