#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Inforamtion

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import json
import httplib
import sys


class NovaAuth:

    def __init__(self, tur_arg=None):
        self=None

    def osauth(self, tur_arg):
        if tur_arg.rax_auth == 'LON':
            tur_arg.region = tur_arg.rax_auth
            if tur_arg.auth_url:
                print 'Using Override Auth URL to\t:', tur_arg.auth_url
                authurl = tur_arg.auth_url
            else:
                authurl = 'lon.identity.api.rackspacecloud.com'
        elif tur_arg.rax_auth == 'DFW' or tur_arg.rax_auth == 'ORD':
            tur_arg.region = tur_arg.rax_auth
            if tur_arg.auth_url:
                print 'Using Override Auth URL to\t:', tur_arg.auth_url
                authurl = tur_arg.auth_url
            else:
                authurl = 'identity.api.rackspacecloud.com'
        elif not tur_arg.rax_auth:
            if not tur_arg.region:
                sys.exit('FAIL\t: You have to specify a Region along with an Auth URL')
            if tur_arg.auth_url:
                print 'Using Region\t:', tur_arg.region
                print 'Using Auth URL\t:', tur_arg.auth_url
                authurl = tur_arg.auth_url
            else:
                sys.exit('FAIL\t: You have to specify an Auth URL along with the Region')
        if tur_arg.apikey:
            jsonreq = \
                json.dumps({'auth': {'RAX-KSKEY:apiKeyCredentials': {'username': tur_arg.user,
                           'apiKey': tur_arg.apikey}}})
        elif tur_arg.password:
            jsonreq = \
                json.dumps({'auth': {'passwordCredentials': {'username': tur_arg.user,
                           'password': tur_arg.password}}})
        else:
            sys.exit('ERROR\t: This should have not happened.\nThere was no way to proceed, so I quit.')

        if tur_arg.debug:
            print '\n', self, '\n'
            print 'JSON REQUEST: ' + jsonreq

        conn = httplib.HTTPSConnection(authurl, 443)
        if tur_arg.debug:
            conn.set_debuglevel(1)
        headers = {'Content-type': 'application/json'}
        conn.request('POST', '/v2.0/tokens', jsonreq, headers)
        resp = conn.getresponse()
        readresp = resp.read()
        if resp.status >= 300:
            print '\n', 'REQUEST\t:', jsonreq, headers, authurl
            sys.exit('\n', 'ERROR\t:', resp.status, resp.reason, '\n')
        json_response = json.loads(readresp)
        conn.close()

        if tur_arg.internal:
            print 'MESSAGE\t: Using the Service Network in the', \
                tur_arg.region, 'DC for', authurl

        if tur_arg.debug:
            print 'JSON decoded and pretty'
            print json.dumps(json_response, indent=2)
        details = {}
        try:
            catalogs = json_response['access']['serviceCatalog']
            #print catalogs
            for service in catalogs:
                if service['name'] == 'cloudFiles':
                    for endpoint in service['endpoints']:
                        if tur_arg.rax_auth == 'MULTI':
                            regions = tur_arg.region_multi
                            for region in regions:
                                if endpoint['region'] == region:
                                    if tur_arg.internal:
                                        details[region] = endpoint['internalURL']
                                    else:
                                        details[region] = endpoint['publicURL']
                        else:
                            if endpoint['region'] == tur_arg.region:
                                if tur_arg.internal:
                                    details['endpoint'] = endpoint['internalURL']
                                else:
                                    details['endpoint'] = endpoint['publicURL']
                        details['tenantid'] = endpoint['tenantId']
            details['token'] = json_response['access']['token']['id']
            if tur_arg.debug:
                print '\n', details, '\n'
                print 'Tenant\t\t: ', details['tenantid']
                print 'Token\t\t: ', details['token']
                print 'Endpoint\t: ', details['endpoint']
            return details
                        
        except (KeyError, IndexError):
            print 'Error while getting answers from auth server.\nCheck the endpoint and auth credentials.'
