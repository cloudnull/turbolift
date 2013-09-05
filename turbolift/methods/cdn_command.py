# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os

from turbolift.clouderator import actions
from turbolift import methods
from turbolift import utils
from turbolift.worker import ARGS
from turbolift.worker import LOG


class archive(object):
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

        utils.reporter(
            msg='Toggling CDN on Container %s.' % ARGS.get('container')
        )

        # Package up the Payload
        payload = utils.prep_payload(
            auth=self.auth,
            container=ARGS.get('container', utils.rand_string()),
            source=None,
            args=ARGS
        )

        LOG.debug('PAYLOAD: "%s"', payload)

        # Set the actions class up
        self.go = actions.cloud_actions(payload=payload)

        with methods.spinner():
            objects = self.go.container_lister(url=payload['url'])

            # Perform the upload
            self.action(url=payload['url'],
                        container=payload['c_name'],
                        source=source,
                        u_file=wfile)
