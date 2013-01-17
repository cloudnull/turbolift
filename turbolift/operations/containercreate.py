#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import httplib
import sys
from urllib2 import quote

class CheckAndMakeContainer(object):
    def __init__(self, container, authdata):
        self.container = container
        self.authdata = authdata


    #noinspection PyBroadException
    def container_create(self):
        """
        Create a container if the container specified on the command line did not already exist.
        """
        try:
            endpoint = self.authdata['endpoint'].split('/')[2]
            headers = {'X-Auth-Token': self.authdata['token']}
            filepath = '/v1/%s/%s' % (self.authdata['tenantid'], quote(self.container))
            conn = httplib.HTTPSConnection(endpoint, 443)
            conn.request('HEAD', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()
            status_codes = (resp.status, resp.reason, self.container)

            if resp.status == 404:
                print '\nMESSAGE\t: %s %s The Container "%s" does not Exist' % status_codes
                conn.request('PUT', filepath, headers=headers)
                resp = conn.getresponse()
                resp.read()

                if resp.status >= 300:
                    print '\nERROR\t: %s %s "%s"\n' % status_codes
                    sys.exc_info()
                print '\nCREATING CONTAINER\t: "%s"\nCONTAINER STATUS\t: %s %s' % status_codes
            conn.close()

        except:
            print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]