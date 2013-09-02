"""Utilities For Authenticating against All Openstack / Rax Clouds."""

import httplib
import traceback

import turbolift as clds
from turbolift import info
from turbolift.worker import LOG
from turbolift.worker import ARGS
from turbolift import utils


def parse_reqtype():
    """Setup our Authentication POST.

    username and setup are only used in APIKEY/PASSWORD Authentication
    """

    setup = {'username': ARGS.get('os_user')}
    if ARGS.get('os_token') is not None:
        auth_body = {'auth': {'token': {'id': ARGS.get('os_token')},
                              'tenantName': ARGS.get('os_tenant')}}
    elif ARGS.get('os_apikey') is not None:
        prefix = 'RAX-KSKEY:apiKeyCredentials'
        setup['apiKey'] = ARGS.get('os_apikey')
        auth_body = {'auth': {prefix: setup}}
    elif ARGS.get('os_password') is not None:
        prefix = 'passwordCredentials'
        setup['password'] = ARGS.get('os_password')
        auth_body = {'auth': {prefix: setup}}
    else:
        LOG.error(traceback.format_exc())
        raise AttributeError('No Password, APIKey, or Token Specified')
    LOG.debug('AUTH Request Type > %s', auth_body)
    return auth_body


def get_surl(region, cf_list, lookup):
    """ Lookup a service URL.

    :param region:
    :param cf_list:
    :param lookup:
    :return net:
    """

    for srv in cf_list:
        if region in srv.get('region'):
            net = utils.parse_url(url=srv.get(lookup))
            return net
    else:
        raise clds.SystemProblem(
            'Region "%s" was not found in your Service Catalog.' % region
        )



def parse_auth_response(auth_response):
    """Parse the auth response and return the tenant, token, and username.

    :param auth_response: the full object returned from an auth call
    :returns: tuple (token, tenant, username, internalurl, externalurl, cdnurl)
    """

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
        raise clds.NoTenantIdFound('When attempting to grab the '
                                   'tenant or user nothing was found.')

    scat = access.pop('serviceCatalog')
    for srv in scat:
        if srv.get('name') in ('cloudFilesCDN', 'cloudFiles', 'swift'):
            if srv.get('name') == 'cloudFilesCDN':
                cdn = srv.get('endpoints')
            if srv.get('name') == 'cloudFiles':
                cfl = srv.get('endpoints')

    if ARGS.get('os_region') is not None:
        region = ARGS.get('os_region')
    elif ARGS.get('os_rax_auth') is not None:
        region = ARGS.get('os_rax_auth')
    else:
        raise clds.SystemProblem('No Region Set')

    if cfl is not None:
        inet = get_surl(region=region, cf_list=cfl, lookup='internalURL')
        enet = get_surl(region=region, cf_list=cfl, lookup='publicURL')

    if cdn is not None:
        cnet = get_surl(region=region, cf_list=cdn, lookup='publicURL')

    return token, tenant, user, inet, enet, cnet, cfl


def parse_region():
    """Pull region/auth url information from context."""

    base_auth_url = 'identity.api.rackspacecloud.com/v2.0/tokens'

    if ARGS.get('os_region'):
        region = ARGS.get('os_region')
    elif ARGS.get('os_rax_auth'):
        region = ARGS.get('os_rax_auth')
    else:
        raise clds.SystemProblem('You Are required to specify a REGION')

    if region is 'LON':
        return ARGS.get('os_auth_url', 'lon.%s' % base_auth_url), True
    elif region.lower() in info.__rax_regions__:
        return ARGS.get('os_auth_url', '%s' % base_auth_url), True
    else:
        if ARGS.get('os_auth_url'):
            if 'racksapce' in ARGS.get('os_auth_url'):
                return ARGS.get('os_auth_url', '%s' % base_auth_url), True
            else:
                return ARGS.get('os_auth_url'), False
        else:
            LOG.error('FAILURE: No Region Found. ARGS DUMP:\t %s', ARGS)
            raise clds.AuthenticationProblem('You Are required to specify a'
                                             ' REGION and an AUTHURL')


def request_process(aurl, req):
    """Perform HTTP(s) request based on Provided Params.

    :param aurl:
    :param req:
    :param https:
    :return read_resp:
    """

    conn = utils.open_connection(url=aurl)

    # Make the request for authentication
    try:
        _method, _url, _body, _headers = req
        conn.request(method=_method, url=_url, body=_body, headers=_headers)
        resp = conn.getresponse()
    except Exception as exc:
        LOG.error('Not able to perform Request ERROR: %s', exc)
        raise AttributeError("Failure to perform Authentication %s ERROR:\n%s"
                             % (exc, traceback.format_exc()))
    else:
        resp_read = resp.read()
        status_code = resp.status
        if status_code >= 300:
            LOG.error('HTTP connection exception: '
                      'Response %s - Response Code %s\n%s',
                      resp_read, status_code, traceback.format_exc())
            raise httplib.HTTPException('Failed to authenticate %s'
                                        % status_code)

        LOG.debug('Connection successful MSG: %s - STATUS: %s', resp.reason,
                  resp.status)
        return resp_read
    finally:
        conn.close()
