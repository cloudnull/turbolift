"""Perform Openstack Authentication."""

import json

from turbolift import exceptions
from turbolift.authentication import utils

from cloudlib import logger


LOG = logger.getLogger('turbolift')


def authenticate(job_args):
    """Authentication For Openstack API.

    Pulls the full Openstack Service Catalog Credentials are the Users API
    Username and Key/Password.

    Set a DC Endpoint and Authentication URL for the OpenStack environment
    """

    # Load any authentication plugins as needed
    job_args = utils.check_auth_plugin(job_args)

    # Set the auth version
    auth_version = utils.get_authversion(job_args=job_args)

    # Define the base headers that are used in all authentications
    auth_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    auth_headers.update(job_args['base_headers'])

    if auth_version == 'v1.0':
        auth = utils.V1Authentication(job_args=job_args)
        auth_headers.update(auth.get_headers())
        LOG.debug('Request Headers: [ %s ]', auth_headers)

        auth_url = job_args['os_auth_url']
        LOG.debug('Parsed Auth URL: [ %s ]', auth_url)

        auth_kwargs = {
            'url': auth_url,
            'headers': auth_headers
        }
    else:
        auth = utils.OSAuthentication(job_args=job_args)
        auth_url = auth.parse_region()
        LOG.debug('Parsed Auth URL: [ %s ]', auth_url)

        auth_json = auth.parse_reqtype()
        LOG.debug('Request Headers: [ %s ]', auth_headers)

        auth_body = json.dumps(auth_json)
        LOG.debug('Request JSON: [ %s ]', auth_body)

        auth_kwargs = {
            'url': auth_url,
            'headers': auth_headers,
            'body': auth_body
        }

    auth_resp = auth.auth_request(**auth_kwargs)
    if auth_resp.status_code >= 300:
        raise exceptions.AuthenticationProblem(
            'Authentication Failure, Status: [ %s ] Reason: [ %s ]',
            auth_resp.status_code,
            auth_resp.reason
        )
    else:
        return auth.parse_auth_response(auth_resp)
