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
import sys

import turbolift as clds
from turbolift import methods
from turbolift import utils
from turbolift.clouderator import actions
from turbolift.worker import ARGS
from turbolift.worker import LOG


class list(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Retrieve a long list of all files in a container."""

        # Package up the Payload
        payload = utils.prep_payload(
            auth=self.auth,
            container=ARGS.get('container'),
            source=None,
            args=ARGS
        )
        self.go = actions.cloud_actions(payload=payload)
        self.action = getattr(self.go, 'object_lister')

        if ARGS.get('verbose'):
            LOG.info(
                'Accessing API for a list of Objects in %s', payload['c_name']
            )

        if ARGS.get('debug'):
            LOG.debug('PAYLOAD\t: "%s"', payload)

        with methods.spinner():
            objects = self.action(url=payload['url'],
                                  container=payload['c_name'])

        # Count the number of objects returned.
        if objects is False:
            utils.reporter(msg='No Container found.')
        elif objects is not None:
            num_files = len(objects)
            if num_files < 1:
                utils.reporter(msg='No Objects found.')
            else:
                count = len(objects)
                for obj in objects:
                    utils.reporter(
                        msg=('size: %s (bytes) - name: %s '
                             % (obj.get('bytes'), obj.get('name')))
                    )
                utils.reporter(
                    msg='You have %s objects in the container' % count
                )
        else:
            utils.reporter(msg='No Objects found.')
