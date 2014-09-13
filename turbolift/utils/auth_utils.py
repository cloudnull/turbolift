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
import traceback
import urlparse

import turbolift as turbo
import turbolift.utils.http_utils as http

from turbolift import ARGS
from turbolift import info
from turbolift.logger import logger


LOG = logger.getLogger('turbolift')
AUTH_VERSION_MAP = {
    'V1': 'v1.0',
    'v1': 'v1.0',
    'v1.0': 'v1.0',
    'V1.0': 'v1.0',
    '1': 'v1.0',
    '1.0': 'v1.0',
    'V2': 'v2.0',
    'v2': 'v2.0',
    'v2.0': 'v2.0',
    'V2.0': 'v2.0',
    '2': 'v2.0',
    '2.0': 'v2.0',
}


def auth_request(url, headers=None, body=None):
    """Perform auth request for token."""
    headers = headers or {}
    body = body or json.dumps({})
    if get_authversion() == 'v1.0':
        # shouldnt need to allow 'stream'
        return http.get_request(url, headers, None)
    else:
        # shouldnt need to allow 'rpath'
        return http.post_request(url, headers, body=body)


def get_headers():
    """Setup headers for authentication request."""

    if get_authversion() == 'v1.0':
        if all([ARGS.get(s) for s in ('st_user', 'st_key')]):
            return {
                'X-Auth-User': ARGS['st_user'],
                'X-Auth-Key': ARGS['st_key']
            }
        else:
            LOG.error(traceback.format_exc())
            raise AttributeError('Missing Password, APIKey, Token, or User')


def parse_reqtype():
    """Setup our Authentication POST.

    username and setup are only used in APIKEY/PASSWORD Authentication
    """

    if get_authversion() == 'v1.0':
        return
    else:
        setup = {'username': ARGS.get('os_user')}
        if ARGS.get('os_token') is not None:
            auth_body = {'auth': {'token': {'id': ARGS.get('os_token')}}}
        elif ARGS.get('os_password') is not None:
            prefix = 'passwordCredentials'
            setup['password'] = ARGS.get('os_password')
            auth_body = {'auth': {prefix: setup}}
        elif ARGS.get('os_apikey') is not None:
            prefix = 'RAX-KSKEY:apiKeyCredentials'
            setup['apiKey'] = ARGS.get('os_apikey')
            auth_body = {'auth': {prefix: setup}}
        else:
            LOG.error(traceback.format_exc())
            raise AttributeError('No Password, APIKey, or Token Specified')

        if ARGS.get('os_tenant'):
            auth_body['auth']['tenantName'] = ARGS.get('os_tenant')

        LOG.debug('AUTH Request Type > %s', auth_body)
        return auth_body


def get_authversion():
    """Get or infer the auth version."""

    authversion = ARGS.get('auth_version')
    authversion = AUTH_VERSION_MAP.get(authversion) or authversion
    if authversion:
        supported = ['v1.0', 'v2.0']
        if authversion not in supported:
            raise ValueError("Auth Version must be one of %s."
                             % supported)
    else:
        # infer version if possible else v2.0
        if any((ARGS.get(s) for s in ('st_auth', 'st_user', 'st_key'))):
            authversion = 'v1.0'
        elif '/v1.0' in ARGS.get('os_auth_url', ''):
            raise ValueError("Specify v1 auth endpoint with 'st_auth'"
                             "instead of 'os_auth_url'")
        elif '/v2.0' in ARGS.get('st_auth', ''):
            raise ValueError("Specify v2 auth endpoint with 'os_auth_url'"
                             "instead of 'st_auth'")
        else:
            authversion = 'v2.0'

    if authversion == 'v1.0':
        if not ARGS.get('st_auth'):
            raise AttributeError("Specify the v1 auth endpoint "
                                 "with 'st_auth'")
    ARGS['auth_version'] = authversion
    return authversion


def get_surl(region, cf_list, lookup):
    """Lookup a service URL.

    :param region:
    :param cf_list:
    :param lookup:
    :return net:
    """

    for srv in cf_list:
        region_get = srv.get('region')
        lookup_get = srv.get(lookup)
        if any([region in region_get, region.lower() in region_get]):
            if lookup_get is None:
                return None
            else:
                return http.parse_url(url=lookup_get)
    # TODO(samstav): No break statement in for loop...
    # remove 'else'
    else:
        raise turbo.SystemProblem(
            'Region "%s" was not found in your Service Catalog.' % region
        )


def _parse_v2_auth_response(auth_response):
    """Parse the auth response and return the tenant, token, and username.

    :param auth_response: the full object returned from an auth call
    :returns: tuple (token, tenant, username, internalurl, externalurl, cdnurl)
    """
    try:
        auth_response = auth_response.json()
    except AttributeError:
        pass
    else:
        LOG.debug('Authentication Response Body %s', auth_response)

    def _service_ep(scat, types_list):
        for srv in scat:
            if srv.get('name') in types_list:
                index_id = types_list.index(srv.get('name'))
                index = types_list[index_id]
                if srv.get('name') == index:
                    return srv.get('endpoints')
        else:
            return None

    access = auth_response.get('access')
    token = access.get('token').get('id')

    if 'tenant' in access.get('token'):
        tenant = access.get('token').get('tenant').get('name')
        user = access.get('user').get('name')
    elif 'user' in access:
        tenant = None
        user = access.get('user').get('name')
    else:
        LOG.error('No Token Found to Parse.\nHere is the DATA: %s\n%s',
                  auth_response, traceback.format_exc())
        raise turbo.NoTenantIdFound('When attempting to grab the '
                                    'tenant or user nothing was found.')

    if ARGS.get('os_rax_auth') is not None:
        region = ARGS.get('os_rax_auth')
    elif ARGS.get('os_hp_auth') is not None:
        if ARGS.get('os_tenant') is None:
            raise turbo.NoTenantIdFound(
                'You need to have a tenant set to use HP Cloud'
            )
        region = ARGS.get('os_hp_auth')
    elif ARGS.get('os_region') is not None:
        region = ARGS.get('os_region')
    else:
        raise turbo.SystemProblem('No Region Set')

    scat = access.pop('serviceCatalog')

    cfl = _service_ep(scat, info.__srv_types__)
    cdn = _service_ep(scat, info.__cdn_types__)

    if cfl is not None:
        inet = get_surl(region=region, cf_list=cfl, lookup='internalURL')
        enet = get_surl(region=region, cf_list=cfl, lookup='publicURL')
    else:
        need_tenant = ' Maybe you need to specify "os-tenant"?'
        gen_message = ('No Service Endpoints were found for use '
                       'with Swift. If you have Swift available to you, '
                       'Check Your Credentials and/or Swift\'s '
                       'availability using Token Auth.')
        if ARGS.get('os_tenant') is None:
            gen_message += need_tenant
        raise turbo.SystemProblem(gen_message)

    if cdn is not None:
        cnet = get_surl(region=region, cf_list=cdn, lookup='publicURL')
    else:
        cnet = None

    return token, tenant, user, inet, enet, cnet, cfl


def parse_auth_response(auth_response):
    """Parse the auth response and return the tenant, token, and username.

    :param auth_response: the full object returned from an auth call
    :returns: tuple (token, tenant, username, internalurl, externalurl, cdnurl)
    """

    if get_authversion() == 'v1.0':
        LOG.debug('Authentication Response Headers %s', auth_response.headers)
        token = auth_response.headers['x-auth-token']

        inet = urlparse.urlparse(auth_response.headers['x-storage-url'])
        acfep = inet
        enet = inet
        cnet = None
        tenant = None
        user = ARGS['st_user']
        return token, tenant, user, inet, enet, cnet, acfep
    else:
        return _parse_v2_auth_response(auth_response)


def _parse_v2_region():
    """Pull region/auth url information from context."""
    if ARGS.get('os_rax_auth'):
        region = ARGS.get('os_rax_auth')
        auth_url = 'identity.api.rackspacecloud.com/v2.0/tokens'
        if region is 'LON':
            return ARGS.get('os_auth_url', 'https://lon.%s' % auth_url)
        elif region.lower() in info.__rax_regions__:
            return ARGS.get('os_auth_url', 'https://%s' % auth_url)
        else:
            raise turbo.SystemProblem('No Known RAX Region Was Specified')
    elif ARGS.get('os_hp_auth'):
        region = ARGS.get('os_hp_auth')
        auth_url = 'https://%s.identity.hpcloudsvc.com:35357/v2.0/tokens'
        if region.lower() in info.__hpc_regions__:
            return ARGS.get('os_auth_url', auth_url % region)
        else:
            raise turbo.SystemProblem('No Known HP Region Was Specified')
    elif 'os_auth_url' in ARGS:
        auth_url = ARGS.get('os_auth_url')
        if not auth_url.endswith('/tokens'):
            auth_url = '%s/tokens' % auth_url
        return auth_url
    else:
        raise turbo.SystemProblem(
            'You Are required to specify an Auth URL, Region or Plugin'
        )


def parse_region():
    """Pull region/auth url information from context."""

    authversion = get_authversion()

    if authversion == 'v1.0':
        return ARGS['st_auth']
    else:
        return _parse_v2_region()
