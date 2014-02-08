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
    try:
        auth_resp = http.post_request(
            url=a_url, headers=headers, body=auth_json_req
        )
        if auth_resp.status_code >= 300:
            raise SystemExit(
                'Authentication Failure, %s %s' % (auth_resp.status_code,
                                                   auth_resp.reason)
            )
    except ValueError as exp:
        LOG.error('Authentication Failure %s\n%s', exp, traceback.format_exc())
        raise turbo.SystemProblem('JSON Decode Failure. ERROR: %s' % exp)
    else:
        LOG.debug('POST Authentication Response %s', auth_resp.json())
        auth_info = auth.parse_auth_response(auth_resp.json())
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
