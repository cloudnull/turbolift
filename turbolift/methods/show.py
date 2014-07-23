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

import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions


class Show(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Retrieve a long list of all files in a container."""

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=None,
            source=None,
            args=ARGS
        )

        # Prep Actions.
        self.go = actions.CloudActions(payload=payload)

        report.reporter(
            msg='PAYLOAD : "%s"' % json.dumps(payload, indent=2),
            prt=False,
            lvl='debug',
        )

        with multi.spinner():
            if ARGS.get('cdn_info'):
                url = payload['cnet']
            else:
                url = payload['url']
            message = self.go.detail_show(url=url)

        try:
            if message.status_code != 404:
                report.reporter(msg='Object Found...')
                report.reporter(
                    msg=report.print_virt_table(dict(message.headers)),
                    log=False
                )
            else:
                report.reporter(msg='Nothing Found...')
        except ValueError as exp:
            report.reporter(
                msg=('Non-hashable Type, Likley Item is not found.'
                     ' Additional Data: %s' % exp)
            )
