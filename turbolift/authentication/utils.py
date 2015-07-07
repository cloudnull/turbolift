# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import traceback
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from cloudlib import logger
from cloudlib import http

import turbolift
from turbolift import exceptions
from turbolift import utils as baseutils


LOG = logger.getLogger('turbolift')
AUTH_VERSION_MAP = {
    'v1.0': ['V1', 'v1', 'v1.0', 'V1.0', '1', '1.0', '1.1'],
    'v2.0': ['V2', 'v2', 'v2.0', 'V2.0', '2', '2.0'],
    'v3.0': ['V3', 'v3', 'v3.0', 'V3.0', '3', '3.0']
}


def check_auth_plugin(job_args):
    _plugins = job_args.get('auth_plugins')
    for name, value in turbolift.auth_plugins(auth_plugins=_plugins).items():
        auth_plugin = job_args.get(name)
        if auth_plugin:
            value.pop('args', None)
            job_args.update(value)
            job_args['os_auth_url'] = value.get('os_auth_url')

            if baseutils.check_basestring(item=auth_plugin):
                job_args['os_region'] = auth_plugin % {
                    'region': auth_plugin
                }

            LOG.debug('Auth Plugin Loaded: [ %s ]', name)
            return job_args
    else:
        return job_args


def get_authversion(job_args):
    """Get or infer the auth version.

    Based on the information found in the *AUTH_VERSION_MAP* the authentication
    version will be set to a correct value as determined by the
    **os_auth_version** parameter as found in the `job_args`.

    :param job_args: ``dict``
    :returns: ``str``
    """

    _version = job_args.get('os_auth_version')
    for version, variants in AUTH_VERSION_MAP.items():
        if _version in variants:
            authversion = job_args['os_auth_version'] = version
            return authversion
    else:
        raise exceptions.AuthenticationProblem(
            "Auth Version must be one of %s.",
            list(AUTH_VERSION_MAP.keys())
        )


def get_service_url(region, endpoint_list, lookup):
    """Lookup a service URL from the *endpoint_list*.

    :param region: ``str``
    :param endpoint_list: ``list``
    :param lookup: ``str``
    :return: ``object``
    """

    for endpoint in endpoint_list:
        region_get = endpoint.get('region', '')
        if region.lower() == region_get.lower():
            return http.parse_url(url=endpoint.get(lookup))
    else:
        raise exceptions.AuthenticationProblem(
            'Region "%s" was not found in your Service Catalog.',
            region
        )


class V1Authentication(object):
    def __init__(self, job_args):
        self.job_args = job_args
        self.req = http.MakeRequest()

    def auth_request(self, url, headers):
        return self.req.get(url, headers)

    def get_headers(self):
        """Setup headers for authentication request."""

        try:
            return {
                'X-Auth-User': self.job_args['os_user'],
                'X-Auth-Key': self.job_args['os_apikey']
            }
        except KeyError as exp:
            raise exceptions.AuthenticationProblem(
                'Missing Credentials. Error: %s',
                exp
            )

    @staticmethod
    def parse_auth_response(auth_response):
        """Parse the auth response and return the tenant, token, and username.

        :param auth_response: the full object returned from an auth call
        :returns: ``dict``
        """

        auth_dict = dict()
        LOG.debug('Authentication Headers %s', auth_response.headers)
        try:
            auth_dict['os_token'] = auth_response.headers['x-auth-token']
            auth_dict['storage_url'] = urlparse.urlparse(
                auth_response.headers['x-storage-url']
            )
        except KeyError as exp:
            raise exceptions.AuthenticationProblem(
                'No token was found in the authentication response. Please'
                ' check your auth URL, your credentials, and your set auth'
                ' version. Auth Headers: [ %s ] Error: [ %s ]',
                auth_response.headers,
                exp
            )
        else:
            return auth_dict


class OSAuthentication(object):
    def __init__(self, job_args):
        self.job_args = job_args
        self.req = http.MakeRequest()

    def auth_request(self, url, headers, body):
        """Perform auth request for token."""

        return self.req.post(url, headers, body=body)

    def parse_reqtype(self):
        """Return the authentication body."""

        if self.job_args['os_auth_version'] == 'v1.0':
            return dict()
        else:
            setup = {
                'username': self.job_args.get('os_user')
            }

            # Check if any prefix items are set. A prefix should be a
            #  dictionary with keys matching the os_* credential type.
            prefixes = self.job_args.get('os_prefix')

            if self.job_args.get('os_token') is not None:
                auth_body = {
                    'auth': {
                        'token': {
                            'id': self.job_args.get('os_token')
                        }
                    }
                }
                if not self.job_args.get('os_tenant'):
                    raise exceptions.AuthenticationProblem(
                        'To use token auth you must specify the tenant id. Set'
                        ' the tenant ID with [ --os-tenant ]'
                    )
            elif self.job_args.get('os_password') is not None:
                setup['password'] = self.job_args.get('os_password')
                if prefixes:
                    prefix = prefixes.get('os_password')
                    if not prefix:
                        raise NotImplementedError(
                            'the `password` method is not implemented for this'
                            ' auth plugin'
                        )
                else:
                    prefix = 'passwordCredentials'
                auth_body = {
                    'auth': {
                        prefix: setup
                    }
                }
            elif self.job_args.get('os_apikey') is not None:
                setup['apiKey'] = self.job_args.get('os_apikey')
                if prefixes:
                    prefix = prefixes.get('os_apikey')
                    if not prefix:
                        raise NotImplementedError(
                            'the `apikey` method is not implemented for this'
                            ' auth plugin'
                        )
                else:
                    prefix = 'apiKeyCredentials'
                auth_body = {
                    'auth': {
                        prefix: setup
                    }
                }
            else:
                raise exceptions.AuthenticationProblem(
                    'No Password, APIKey, or Token Specified'
                )

            if self.job_args.get('os_tenant'):
                auth = auth_body['auth']
                auth['tenantName'] = self.job_args.get('os_tenant')

            LOG.debug('AUTH Request body: [ %s ]', auth_body)
            return auth_body

    @staticmethod
    def _service_endpoints(service_catalog, types_list):
        for entry in service_catalog:
            for type_name in types_list:
                if entry.get('type') == type_name:
                    return entry.get('endpoints')
        else:
            return list()

    def parse_auth_response(self, auth_response):
        """Parse the auth response and return the tenant, token, and username.

        :param auth_response: the full object returned from an auth call
        :returns: ``dict``
        """

        auth_dict = dict()
        auth_response = auth_response.json()
        LOG.debug('Authentication Response Body [ %s ]', auth_response)

        access = auth_response.get('access')
        access_token = access.get('token')
        access_tenant = access_token.get('tenant')
        access_user = access.get('user')

        auth_dict['os_token'] = access_token.get('id')
        auth_dict['os_tenant'] = access_tenant.get('name')
        auth_dict['os_user'] = access_user.get('name')

        if not auth_dict['os_token']:
            raise exceptions.AuthenticationProblem(
                'When attempting to grab the tenant or user nothing was'
                ' found. No Token Found to Parse. Here is the DATA: [ %s ]'
                ' Stack Trace [ %s ]',
                auth_response,
                traceback.format_exc()
            )

        region = self.job_args.get('os_region')
        print(region)
        if not region:
            raise exceptions.SystemProblem('No Region Set')

        service_catalog = access.pop('serviceCatalog')

        # Get the storage URL
        object_endpoints = self._service_endpoints(
            service_catalog=service_catalog,
            types_list=turbolift.__srv_types__
        )

        # In the legacy internal flag is set override the os_endpoint_type
        #  TODO(cloudnull) Remove this in future releases
        if 'internal' in self.job_args and self.job_args['internal']:
            LOG.warn(
                'The use of the ``--internal`` flag has been deprecated and'
                ' will be removed in future releases. Please use the'
                ' ``--os-endpoint-type`` flag and set the type name'
                ' instead. In the case of using snet (service net) this is'
                ' generally noted as "internalURL". Example setting:'
                ' ``--os-endpoint-type internalURL``'
            )
            self.job_args['os_endpoint_type'] = 'internalURL'

        auth_dict['storage_url'] = get_service_url(
            region=region,
            endpoint_list=object_endpoints,
            lookup=self.job_args['os_endpoint_type']
        )

        # Get the CDN URL
        cdn_endpoints = self._service_endpoints(
            service_catalog=service_catalog, types_list=turbolift.__cdn_types__
        )

        if cdn_endpoints:
            auth_dict['cdn_storage_url'] = get_service_url(
                region=region,
                endpoint_list=cdn_endpoints,
                lookup=self.job_args['cdn_endpoint_type']
            )

        return auth_dict

    def parse_region(self):
        """Pull region/auth url information from context."""

        try:
            auth_url = self.job_args['os_auth_url']
            if 'tokens' not in auth_url:
                if not auth_url.endswith('/'):
                    auth_url = '%s/' % auth_url
                auth_url = urlparse.urljoin(auth_url, 'tokens')
            return auth_url
        except KeyError:
            raise exceptions.AuthenticationProblem(
                'You Are required to specify an Auth URL, Region or Plugin'
            )
