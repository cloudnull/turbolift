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

import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions


class CdnCommand(object):
    """Setup and run the archive Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """This is the archive method.

        Uses archive (TAR) feature to compress files and then upload the
        TAR Ball to a specified container.
        """

        report.reporter(
            msg='Toggling CDN on Container %s.' % ARGS.get('container')
        )

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('container', basic.rand_string()),
            source=None,
            args=ARGS
        )

        report.reporter(
            msg='PAYLOAD : "%s"' % json.dumps(payload, indent=2),
            prt=False,
            lvl='debug',
        )

        # Set the actions class up
        self.go = actions.CloudActions(payload=payload)

        with multi.spinner():
            if ARGS.get('purge'):
                for obj in ARGS.get('purge'):
                    # Perform the purge
                    self.go.container_cdn_command(url=payload['cnet'],
                                                  container=payload['c_name'],
                                                  sfile=obj)
            else:
                self.go.container_cdn_command(url=payload['cnet'],
                                              container=payload['c_name'])
