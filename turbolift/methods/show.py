# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from turbolift.clouderator import actions
from turbolift import methods
from turbolift import utils
from turbolift.worker import ARGS
from turbolift.worker import LOG


class show(object):
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
            container=None,
            source=None,
            args=ARGS
        )

        # Prep Actions.
        self.go = actions.cloud_actions(payload=payload)

        LOG.debug('PAYLOAD\t: "%s"', payload)

        with methods.spinner():
            for retry in utils.retryloop(attempts=ARGS.get('error_retry'),
                                         delay=1):
                url = payload['url']
                conn = utils.open_connection(url=url)
                if ARGS.get('object') is not None:
                    rpath = self.go._quoter(url=url.path,
                                            cont=ARGS.get('container'),
                                            ufile=ARGS.get('object'))
                else:
                    rpath = self.go._quoter(url=url.path,
                                            cont=ARGS.get('container'))

                resp = self.go._header_getter(conn=conn,
                                              rpath=rpath,
                                              fheaders=payload['headers'],
                                              retry=retry)
                if resp.status == 404:
                    utils.reporter(msg='Nothing found.')
                else:
                    utils.reporter(msg='Object found.')
                    for _re in resp.getheaders():
                        utils.reporter(msg='%s:\t%s' % _re)
