# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

class FakeHttpResponse(object):
    """Setup a FAKE http response."""

    def __init__(self, status, reason, headers, body):
        """Accept user input and return a response for HTTP

        :param status:
        :param reason:
        :param headers:
        :param body:
        :return body:
        :return headers:
        """

        self.body = body
        self.status = status
        self.reason = reason
        self.headers = headers

    def request(self):
        pass

    def getresponse(self):
        pass

    def read(self):
        """Return HTTP body."""

        return self.body

    def getheaders(self):
        """Return HTTP Headers."""

        return self.headers


class ParseResult(object):
    scheme = 'https'
    netloc = 'TEST.url'
    path = '/v2.0/tokens'
    params = ''
    query = ''
    fragment = ''
