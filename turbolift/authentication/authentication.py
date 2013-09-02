"""Perform Openstack Authentication."""

import json
import traceback

import turbolift as clds
from turbolift import utils
from turbolift.authentication import auth_utils
from turbolift.worker import LOG


def authenticate():
    """Authentication For Openstack API.

    Pulls the full Openstack Service Catalog Credentials are the Users API
    Username and Key/Password "osauth" has a Built in Rackspace Method for
    Authentication

    Set a DC Endpoint and Authentication URL for the OpenStack environment

    :param auth_dict: required parameters are auth_url
    """

    # Setup the request variables
    url, rax = auth_utils.parse_region()
    a_url = utils.parse_url(url=url, auth=True)
    auth_json = auth_utils.parse_reqtype()

    # remove the prefix for the Authentication URL if Found
    LOG.debug('POST == REQUEST DICT > JSON DUMP %s', auth_json)
    auth_json_req = json.dumps(auth_json)
    headers = {'Content-Type': 'application/json'}

    # Send Request
    request = ('POST', a_url.path, auth_json_req, headers)
    resp_read = auth_utils.request_process(aurl=a_url, req=request)
    LOG.debug('POST Authentication Response %s', resp_read)
    try:
        auth_resp = json.loads(resp_read)
    except ValueError as exp:
        LOG.error('Authentication Failure %s\n%s', exp,
                  traceback.format_exc())
        raise clds.SystemProblem('JSON Decode Failure. ERROR: %s - RESP %s'
                                 % (exp, resp_read))
    else:
        auth_info = auth_utils.parse_auth_response(auth_resp)
        token, tenant, user, inet, enet, cnet, acfep = auth_info
        utils.reporter(
            msg=('API Access Granted. Auth token: %s TenantID: %s Username: %s'
                 % (token, tenant, user)),
            prt=False,
            log=True
        )
        return token, tenant, user, inet, enet, cnet, a_url, acfep
