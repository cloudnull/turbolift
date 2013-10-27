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

import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions
from turbolift import methods


class Archive(object):
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

        # Index Local Files for Upload
        f_indexed = methods.get_local_files()

        if ARGS.get('pattern_match'):
            f_indexed = basic.match_filter(
                idx_list=f_indexed, pattern=ARGS['pattern_match']
            )

        num_files = len(f_indexed)
        report.reporter(msg='MESSAGE: "%s" Files have been found.' % num_files)

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('container', basic.rand_string()),
            source=None,
            args=ARGS
        )

        report.reporter(
            msg='PAYLOAD\t: "%s"' % payload,
            log=True,
            lvl='debug',
            prt=False
        )

        # Set the actions class up
        self.go = actions.CloudActions(payload=payload)
        self.go.container_create(
            url=payload['url'], container=payload['c_name']
        )
        self.action = getattr(self.go, 'object_putter')

        with multi.spinner():
            # Compression Job
            wfile = methods.compress_files(file_list=f_indexed)
            source, name = os.path.split(wfile)
            report.reporter(msg='MESSAGE: "%s" is being uploaded.' % name)

            # Perform the upload
            self.action(url=payload['url'],
                        container=payload['c_name'],
                        source=source,
                        u_file=wfile)

            # Remove the archive unless instructed not too.
            if ARGS.get('no_cleanup') is None:
                basic.remove_file(wfile)
