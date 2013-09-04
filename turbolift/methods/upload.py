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


class upload(object):
    """Setup and run the upload Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """This is the upload method.

        Uses file_upload is to simply upload all files and folders to a
        specified container.
        """

        # Index Local Files for Upload
        f_indexed = methods.get_local_files()
        num_files = len(f_indexed)

        # Get The rate of concurrency
        concurrency = utils.set_concurrency(args=ARGS, file_count=num_files)

        # Package up the Payload
        payload = utils.prep_payload(
            auth=self.auth,
            container=ARGS.get('container', utils.rand_string()),
            source=utils.get_local_source(args=ARGS),
            args=ARGS
        )

        # Load the Queue
        work_q = utils.basic_queue(iters=f_indexed)

        # Set the actions class up
        self.go = actions.cloud_actions(payload=payload)
        self.go._container_create(url=payload['url'],
                                  container=payload['c_name'])
        self.action = getattr(self.go, 'object_putter')

        if ARGS.get('verbose'):
            LOG.info('MESSAGE\t: "%s" Files have been found.', num_files)

        if ARGS.get('debug'):
            LOG.debug('PAYLOAD\t: "%s"', payload)

        with methods.spinner(work_q=work_q):
            utils.worker_proc(job_action=self.uploaderator,
                              num_jobs=num_files,
                              concurrency=concurrency,
                              t_args=payload,
                              queue=work_q)

    def uploaderator(self, work_q, payload):
        """Upload files to CloudFiles -Swift-.

        :param work_q:
        :param payload:
        """

        # Get work from the Queue
        while True:
            wfile = utils.get_from_q(queue=work_q)
            # If Work is None return None
            if wfile is None:
                break
            try:
                source = payload['source']
                container = payload['c_name']
                self.action(url=payload['url'],
                            container=container,
                            source=source,
                            u_file=wfile)
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)
            except EOFError:
                utils.emergency_kill()
