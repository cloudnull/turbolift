# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import json
import httplib
import unittest

import mock

import turbolift

from turbolift.authentication import authentication
from turbolift import tests
from turbolift.utils import auth_utils


FAKE_200_OK = tests.FakeHttpResponse(
    status=200,
    reason='OK',
    headers=[('Foo', 'Bar')],
    body=json.dumps({'message': 'connection response'})
)

FAKE_300_FAILURE = tests.FakeHttpResponse(
    status=300,
    reason='UNAUTHORIZED',
    headers=[('Foo', 'Bar')],
    body=json.dumps({'message': 'connection response'})
)


class TestAuthenticate(unittest.TestCase):
    """Test Authentication Method."""

    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, obj, cls, msg=None):
            if not isinstance(obj, cls):
                standardMsg = '%s is not an instance of %r' % (obj, cls)
                self.fail(self._formatMessage(msg, standardMsg))

    def setUp(self):
        self.srv_cat_json = {
            u"access": {
                u"token": {
                    u"id": u"TEST-ID",
                },
                u"serviceCatalog": [
                    {
                        u"endpoints": [
                            {
                                u"region": u"TEST-REGION",
                                u"tenantId": u"TEST-TENANT-ID",
                                u"publicURL": u"https://TEST.url"
                            }
                        ],
                        u"name": u"cloudFiles"
                    },
                    {
                        u"endpoints": [
                            {
                                u"region": u"TEST-REGION",
                                u"tenantId": u"TEST-TENANT-ID",
                                u"publicURL": u"https://TEST-CDN.url"
                            }
                        ],
                        u"name": u"cloudFilesCDN"
                    }
                ],
                u"user": {
                    u"name": u"TEST-USER"
                }
            }
        }

    def endpoints(self, name):
        access = self.srv_cat_json.get('access')
        scat = access.get('serviceCatalog')

        for srv in scat:
            if srv.get('name') == name:
                return srv.get('endpoints')
        else:
            self.fail()

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_token(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_token': 'TEST-TOKEN'
        }
        expected_return = {
            'auth': {
                'token': {
                    'id': 'TEST-TOKEN'
                }
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_password(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_password': 'TEST-PASSWORD'
        }
        expected_return = {
            'auth': {
                'passwordCredentials': {
                    'username': 'TEST-USER',
                    'password': 'TEST-PASSWORD'
                }
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_apikey(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_apikey': 'TEST-APIKEY'
        }
        expected_return = {
            'auth': {
                'RAX-KSKEY:apiKeyCredentials': {
                    'username': 'TEST-USER',
                    'apiKey': 'TEST-APIKEY'
                }
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_failure(self, mock_log):
        args = {
            'os_user': 'TEST-USER'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            self.assertRaises(AttributeError, auth_utils.parse_reqtype)
            self.assertTrue(mock_log.error.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_token_with_tenant(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_token': 'TEST-TOKEN',
            'os_tenant': 'TEST-TENANT'
        }
        expected_return = {
            'auth': {
                'token': {
                    'id': 'TEST-TOKEN'
                },
                'tenantName': 'TEST-TENANT'
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_password_with_tenant(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_password': 'TEST-PASSWORD',
            'os_tenant': 'TEST-TENANT'
        }
        expected_return = {
            'auth': {
                'passwordCredentials': {
                    'username': 'TEST-USER',
                    'password': 'TEST-PASSWORD'
                },
                'tenantName': 'TEST-TENANT'
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_reqtype_apikey_with_tenant(self, mock_log):
        args = {
            'os_user': 'TEST-USER',
            'os_apikey': 'TEST-APIKEY',
            'os_tenant': 'TEST-TENANT'
        }
        expected_return = {
            'auth': {
                'RAX-KSKEY:apiKeyCredentials': {
                    'username': 'TEST-USER',
                    'apiKey': 'TEST-APIKEY'
                },
                'tenantName': 'TEST-TENANT'
            }
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            ab = auth_utils.parse_reqtype()
            self.assertEqual(ab, expected_return)
            self.assertTrue(mock_log.debug.called)

    def test_get_surl(self):
        cf_return = self.endpoints(name='cloudFiles')
        parsed_url = auth_utils.get_surl(
            region='TEST-REGION', cf_list=cf_return, lookup='publicURL'
        )
        self.assertEqual(parsed_url.scheme, 'https')
        self.assertEqual(parsed_url.netloc, 'TEST.url')

    def test_get_surl_cdn(self):
        cf_return = self.endpoints(name='cloudFilesCDN')
        parsed_url = auth_utils.get_surl(
            region='TEST-REGION', cf_list=cf_return, lookup='publicURL'
        )
        self.assertEqual(parsed_url.scheme, 'https')
        self.assertEqual(parsed_url.netloc, 'TEST-CDN.url')

    def test_get_surl_bad_lookup(self):
        cf_return = self.endpoints(name='cloudFiles')
        parsed_url = auth_utils.get_surl(
            region='TEST-REGION', cf_list=cf_return, lookup='NotThisURL'
        )
        self.assertEqual(parsed_url, None)

    def test_get_surl_not_region_found(self):
        cf_return = self.endpoints(name='cloudFiles')
        kwargs = {
            'region': 'NotThisRegion',
            'cf_list': cf_return,
            'lookup': 'publicURL'
        }
        self.assertRaises(
            turbolift.SystemProblem, auth_utils.get_surl, **kwargs
        )

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_tenant_with_rax_auth(self, mock_log):
        args = {
            'os_rax_auth': 'TEST-REGION'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            srv_cat = self.srv_cat_json.copy()
            srv_cat['access']['token']['tenant'] = {u'name': u'TEST-TENANT'}
            par = auth_utils.parse_auth_response(auth_response=srv_cat)
            self.assertIsInstance(par, tuple)
            self.assertEqual(par[0], 'TEST-ID')
            self.assertEqual(par[1], 'TEST-TENANT')
            self.assertEqual(par[2], 'TEST-USER')
            self.assertEqual(par[3], None)
            self.assertEqual(par[4].scheme, 'https')
            self.assertEqual(par[4].netloc, 'TEST.url')
            self.assertEqual(par[5].scheme, 'https')
            self.assertEqual(par[5].netloc, 'TEST-CDN.url')
            self.assertIsInstance(par[6], list)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_with_rax_auth(self, mock_log):
        args = {
            'os_rax_auth': 'TEST-REGION'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            srv_cat = self.srv_cat_json.copy()
            par = auth_utils.parse_auth_response(auth_response=srv_cat)
            self.assertIsInstance(par, tuple)
            self.assertEqual(par[0], 'TEST-ID')
            self.assertEqual(par[1], None)
            self.assertEqual(par[2], 'TEST-USER')
            self.assertEqual(par[3], None)
            self.assertEqual(par[4].scheme, 'https')
            self.assertEqual(par[4].netloc, 'TEST.url')
            self.assertEqual(par[5].scheme, 'https')
            self.assertEqual(par[5].netloc, 'TEST-CDN.url')
            self.assertIsInstance(par[6], list)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_with_hp_auth(self, mock_log):
        args = {
            'os_hp_auth': 'TEST-REGION',
            'os_tenant': 'TEST-TENANT'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            srv_cat = self.srv_cat_json.copy()
            par = auth_utils.parse_auth_response(auth_response=srv_cat)
            self.assertIsInstance(par, tuple)
            self.assertEqual(par[0], 'TEST-ID')
            self.assertEqual(par[1], None)
            self.assertEqual(par[2], 'TEST-USER')
            self.assertEqual(par[3], None)
            self.assertEqual(par[4].scheme, 'https')
            self.assertEqual(par[4].netloc, 'TEST.url')
            self.assertEqual(par[5].scheme, 'https')
            self.assertEqual(par[5].netloc, 'TEST-CDN.url')
            self.assertIsInstance(par[6], list)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_with_region_auth(self, mock_log):
        args = {
            'os_region': 'TEST-REGION',
            'os_tenant': 'TEST-TENANT'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            srv_cat = self.srv_cat_json.copy()
            par = auth_utils.parse_auth_response(auth_response=srv_cat)
            self.assertIsInstance(par, tuple)
            self.assertEqual(par[0], 'TEST-ID')
            self.assertEqual(par[1], None)
            self.assertEqual(par[2], 'TEST-USER')
            self.assertEqual(par[3], None)
            self.assertEqual(par[4].scheme, 'https')
            self.assertEqual(par[4].netloc, 'TEST.url')
            self.assertEqual(par[5].scheme, 'https')
            self.assertEqual(par[5].netloc, 'TEST-CDN.url')
            self.assertIsInstance(par[6], list)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_with_hp_auth_failure(self, mock_log):
        args = {
            'os_hp_auth': 'TEST-REGION',
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            srv_cat = self.srv_cat_json.copy()
            self.assertRaises(
                turbolift.NoTenantIdFound,
                auth_utils.parse_auth_response,
                srv_cat
            )

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_failure(self, mock_log):
        srv_cat = self.srv_cat_json.copy()
        srv_cat['access'].pop('user')

        self.assertRaises(
            turbolift.NoTenantIdFound,
            auth_utils.parse_auth_response,
            srv_cat
        )
        self.assertTrue(mock_log.error.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    def test_parse_auth_response_no_region_failure(self, mock_log):
        args = {
            'os_tenant': 'TEST-TENANT'
        }
        srv_cat = self.srv_cat_json.copy()
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            self.assertRaises(
                turbolift.SystemProblem,
                auth_utils.parse_auth_response,
                srv_cat
            )

    @mock.patch('turbolift.utils.auth_utils.LOG')
    @mock.patch('turbolift.utils.auth_utils.info.__srv_types__', ['NotFound'])
    @mock.patch('turbolift.utils.auth_utils.info.__cdn_types__', ['NotFound'])
    def test_parse_auth_response_no_cloudfiles_endpoints(self, mock_log):
        args = {
            'os_region': 'TEST-REGION',
            'os_tenant': 'TEST-TENANT'
        }
        srv_cat = self.srv_cat_json.copy()
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            self.assertRaises(
                turbolift.SystemProblem,
                auth_utils.parse_auth_response,
                srv_cat
            )

    def test_parse_region_rax_auth_us(self):
        args = {
            'os_rax_auth': 'ORD'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://identity.api.rackspacecloud.com/v2.0/tokens'
            )

    def test_parse_region_rax_auth_lon_with_auth_url(self):
        args = {
            'os_rax_auth': 'ORD',
            'os_auth_url': 'https://TEST.url'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://TEST.url'
            )

    def test_parse_region_rax_auth_lon(self):
        args = {
            'os_rax_auth': 'LON'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://lon.identity.api.rackspacecloud.com/v2.0/tokens'
            )

    def test_parse_region_rax_auth_us_with_auth_url(self):
        args = {
            'os_rax_auth': 'ORD',
            'os_auth_url': 'https://TEST.url'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://TEST.url'
            )

    def test_parse_region_rax_auth_failure(self):
        args = {
            'os_rax_auth': 'TEST-REGION'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            self.assertRaises(
                turbolift.SystemProblem, auth_utils.parse_region
            )

    def test_parse_region_hp_auth(self):
        args = {
            'os_hp_auth': 'region-b.geo-1'
        }
        au = 'https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/tokens'
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, au
            )

    def test_parse_region_hp_auth_with_auth_url(self):
        args = {
            'os_hp_auth': 'region-b.geo-1',
            'os_auth_url': 'https://TEST.url'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://TEST.url'
            )

    def test_parse_region_hp_auth_failure(self):
        args = {
            'os_hp_auth': 'TEST-REGION'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            self.assertRaises(
                turbolift.SystemProblem, auth_utils.parse_region
            )

    def test_parse_region_with_auth_url(self):
        args = {
            'os_auth_url': 'https://TEST.url'
        }
        with mock.patch('turbolift.utils.auth_utils.ARGS', args):
            url = auth_utils.parse_region()
            self.assertEqual(
                url, 'https://TEST.url'
            )

    def test_parse_region_auth_failure(self):
        with mock.patch('turbolift.utils.auth_utils.ARGS', {}):
            self.assertRaises(
                    turbolift.SystemProblem, auth_utils.parse_region
            )

    @mock.patch('turbolift.utils.auth_utils.LOG')
    @mock.patch('turbolift.utils.auth_utils.http.open_connection')
    def test_request_process(self, mock_conn, mock_log):

        _mock = mock.Mock()
        _mock.getresponse.side_effect = [FAKE_200_OK]
        mock_conn.return_value = _mock

        parsed_url = tests.ParseResult
        post = {
            "auth": {
                'passwordCredentials': {
                    "username": "TEST-USER",
                    "password": "TEST-ID"
                }
            }
        }

        post_request = (
            'POST',
            '/v2.0/tokens',
            str(post),
            {'Content-Type': 'application/json'}
        )

        resp = auth_utils.request_process(
            aurl=parsed_url, req=post_request
        )
        self.assertEqual(resp, '{"message": "connection response"}')
        self.assertTrue(mock_log.debug.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    @mock.patch('turbolift.utils.auth_utils.http.open_connection')
    def test_request_process_bad_status(self, mock_conn, mock_log):

        _mock = mock.Mock()
        _mock.getresponse.side_effect = [FAKE_300_FAILURE]
        mock_conn.return_value = _mock

        parsed_url = tests.ParseResult
        post = {
            "auth": {
                'passwordCredentials': {
                    "username": "TEST-USER",
                    "password": "TEST-ID"
                }
            }
        }

        post_request = (
            'POST',
            '/v2.0/tokens',
            str(post),
            {'Content-Type': 'application/json'}
        )

        kwargs = {
            'aurl': parsed_url,
            'req': post_request
        }

        self.assertRaises(
            httplib.HTTPException,
            auth_utils.request_process,
            **kwargs
        )
        self.assertTrue(mock_log.error.called)

    @mock.patch('turbolift.utils.auth_utils.LOG')
    @mock.patch('turbolift.utils.auth_utils.http.open_connection')
    def test_request_process_exception(self, mock_conn, mock_log):

        _mock = mock.Mock()
        _mock.getresponse.side_effect = Exception('Died')
        mock_conn.return_value = _mock

        parsed_url = tests.ParseResult
        post = {
            "auth": {
                'passwordCredentials': {
                    "username": "TEST-USER",
                    "password": "TEST-ID"
                }
            }
        }

        post_request = (
            'POST',
            '/v2.0/tokens',
            str(post),
            {'Content-Type': 'application/json'}
        )

        kwargs = {
            'aurl': parsed_url,
            'req': post_request
        }

        self.assertRaises(
            AttributeError,
            auth_utils.request_process,
            **kwargs
        )
        self.assertTrue(mock_log.error.called)
