"""Perform Openstack Authentication."""

import json
import traceback

import turbolift as turbo
import turbolift.utils.auth_utils as auth
import turbolift.utils.http_utils as http
import turbolift.utils.report_utils as report

from turbolift import LOG


def authenticate():
    """Authentication For Openstack API.

    Pulls the full Openstack Service Catalog Credentials are the Users API
    Username and Key/Password "osauth" has a Built in Rackspace Method for
    Authentication

    Set a DC Endpoint and Authentication URL for the OpenStack environment

    :param auth_dict: required parameters are auth_url
    """

    # Setup the request variables
    url = auth.parse_region()
    a_url = http.parse_url(url=url, auth=True)
    auth_json = auth.parse_reqtype()

    # remove the prefix for the Authentication URL if Found
    LOG.debug('POST == REQUEST DICT > JSON DUMP %s', auth_json)
    auth_json_req = json.dumps(auth_json)
    headers = {'Content-Type': 'application/json'}

    # Send Request
    request = ('POST', a_url.path, auth_json_req, headers)
    resp_read = auth.request_process(aurl=a_url, req=request)
    LOG.debug('POST Authentication Response %s', resp_read)
    try:
        auth_resp = json.loads(resp_read)
    except ValueError as exp:
        LOG.error('Authentication Failure %s\n%s', exp,
                  traceback.format_exc())
        raise turbo.SystemProblem('JSON Decode Failure. ERROR: %s - RESP %s'
                                  % (exp, resp_read))
    else:
        auth_info = auth.parse_auth_response(auth_resp)
        token, tenant, user, inet, enet, cnet, acfep = auth_info
        report.reporter(
            msg=('API Access Granted. TenantID: %s Username: %s'
                 % (tenant, user)),
            prt=False,
            log=True
        )
        return token, tenant, user, inet, enet, cnet, a_url, acfep


def get_new_token():
    """Authenticate and return only a new token.

    :return token:
    """

    return authenticate()[0]
