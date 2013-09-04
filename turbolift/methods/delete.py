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


class delete(object):
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

        LOG.info('Attempting Delete of Remote path %s', payload['c_name'])

        if ARGS.get('verbose'):
            LOG.info(
                'Accessing API for a list of Objects in %s', payload['c_name']
            )

        if ARGS.get('debug'):
            LOG.debug('PAYLOAD\t: "%s"', payload)

        # Make 2 passes when deleting objects.
        utils.reporter(
            msg='This operation will make 2 passes when deleting objects.'
        )

        # Multipass Object Delete.
        objects = False
        for _ in range(2):
            utils.reporter(msg='Getting file list')
            with methods.spinner():
                # Get all objects in a Container
                objects = self.action(url=payload['url'],
                                      container=payload['c_name'])

                # Count the number of objects returned.
                if objects is False:
                    utils.reporter(msg='No Container found.')
                    break
                elif objects is not None:
                    num_files = len(objects)
                    if num_files < 1:
                        utils.reporter(msg='No Objects found.')
                        break
                else:
                    utils.reporter(msg='Nothing found.')
                    break

                # Get The rate of concurrency
                concurrency = utils.set_concurrency(args=ARGS,
                                                    file_count=num_files)

                # Load the queue
                obj_list = [obj['name'] for obj in objects]
                if ARGS.get('object_name'):
                    obj_names = ARGS.get('object_name')
                    obj_list = [obj for obj in obj_list if obj in obj_names]
                work_q = utils.basic_queue(obj_list)

            utils.reporter(msg='Performing Object Delete...')
            with methods.spinner(work_q=work_q):
                utils.worker_proc(job_action=self.deleterator,
                                  num_jobs=num_files,
                                  concurrency=concurrency,
                                  t_args=payload,
                                  queue=work_q)

            utils.stupid_hack(wait=2)

        if any([ARGS.get('save_container') is None,
                objects is not False]):
            if not ARGS.get('object_name'):
                utils.reporter(msg='Performing Container Delete.')
                with methods.spinner():
                    self.go.container_deleter(url=payload['url'],
                                              container=payload['c_name'])

    def deleterator(self, work_q, payload):
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
                self.go.object_deleter(url=payload['url'],
                                       container=payload['c_name'],
                                       u_file=wfile)
            except EOFError:
                utils.emergency_kill()
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)
