#!/usr/bin/python
# -*- coding: utf-8 -*-

# - title        : NovaAuth Method
# - description  : Authenticate using the Nova API
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - usage        : executable -> authentication
# - notes        : Authentication script
# - Python       : >= 2.6

"""
License Inforamtion
    
This software has no warranty, it is provided 'as is'. It is your responsibility
to validate the behavior of the routines and its accuracy using the code provided.
Consult the GNU General Public license for further details (see GNU General Public License).
    
http://www.gnu.org/licenses/gpl.html
"""

import json
import httplib
from urllib import quote


class NovaAuth:

    def __init__(self):
        self = None

    def osauth(self, ta):
        self = ta
        if self.rax_auth == 'LON':
            self.region = self.rax_auth
            if self.auth_url:
                print 'Using Override Auth URL to\t:', self.auth_url
                authurl = self.auth_url
            else:
                authurl = 'lon.identity.api.rackspacecloud.com'
        elif self.rax_auth == 'DFW' or self.rax_auth == 'ORD':
            self.region = self.rax_auth
            if self.auth_url:
                print 'Using Override Auth URL to\t:', self.auth_url
                authurl = self.auth_url
            else:
                authurl = 'identity.api.rackspacecloud.com'
        elif self.rax_auth == 'MULTI':
            self.region_multi = ['DFW', 'ORD']
            if self.auth_url:
                print 'Using Override Auth URL to\t:', self.auth_url
                authurl = self.auth_url
            else:
                authurl = 'identity.api.rackspacecloud.com'
        elif not self.rax_auth:
            if not self.region:
                sys.exit('FAIL\t: You have to specify a Region along with an Auth URL')
            if self.auth_url:
                print 'Using Region\t:', self.region
                print 'Using Auth URL\t:', self.auth_url
                authurl = self.auth_url
            else:
                sys.exit('FAIL\t: You have to specify an Auth URL along with the Region')
        if self.apikey:
            jsonreq = \
                json.dumps({'auth': {'RAX-KSKEY:apiKeyCredentials': {'username': self.user,
                           'apiKey': self.apikey}}})
        elif self.password:
            jsonreq = \
                json.dumps({'auth': {'passwordCredentials': {'username': self.user,
                           'password': self.password}}})
        else:
            sys.exit('ERROR\t: This should have not happened.\nThere was no way to proceed, so I quit.')

        if self.veryverbose:
            print '\n', self, '\n'
            print 'JSON REQUEST: ' + jsonreq

        conn = httplib.HTTPSConnection(authurl, 443)
        if self.veryverbose:
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

        if self.internal:
            print 'MESSAGE\t: Using the Service Network in the', \
                self.region, 'DC for', authurl

        if self.veryverbose:
            print 'JSON decoded and pretty'
            print json.dumps(json_response, indent=2)
        details = {}
        try:
            catalogs = json_response['access']['serviceCatalog']
            #print catalogs
            for service in catalogs:
                if service['name'] == 'cloudFiles':
                    for endpoint in service['endpoints']:
                        if self.rax_auth == 'MULTI':
                            regions = self.region_multi
                            for region in regions:
                                if endpoint['region'] == region:
                                    if self.internal:
                                        details[region] = endpoint['internalURL']
                                    else:
                                        details[region] = endpoint['publicURL']
                        else:
                            if endpoint['region'] == self.region:
                                if self.internal:
                                    details['endpoint'] = endpoint['internalURL']
                                else:
                                    details['endpoint'] = endpoint['publicURL']
                        details['tenantid'] = endpoint['tenantId']
            details['token'] = json_response['access']['token']['id']
            if self.veryverbose:
                print '\n', details, '\n'
                print 'Tenant\t\t: ', details['tenantid']
                print 'Token\t\t: ', details['token']
                if self.rax_auth == 'MULTI':
                    print 'Endpoint\t: ', details['DFW']
                    print 'Endpoint\t: ', details['ORD']
                else:
                    print 'Endpoint\t: ', details['endpoint']
        except (KeyError, IndexError):
            print 'Error while getting answers from auth server.\nCheck the endpoint and auth credentials.'
        return details


