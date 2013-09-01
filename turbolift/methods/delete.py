# =============================================================================
# Copyright [2013] [kevin]
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
from turbolift import utils
from turbolift import methods
from turbolift.clouderator import actions
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
        print('This operation will make 2 passes when deleting objects.')
        for _ in range(2):
            print('getting file list')
            with methods.spinner():
                # Get all objects in a Container
                objects = self.action(url=payload['url'],
                                      container=payload['c_name'])

                # Count the number of objects returned.
                if objects is not None:
                    num_files = len(objects)
                    if num_files < 1:
                        print('No Objects found.')
                        break
                else:
                    print('No Objects found.')
                    break

                # Get The rate of concurrency
                concurrency = utils.set_concurrency(args=ARGS,
                                                    file_count=num_files)

                # Load the queue
                obj_list = [obj['name'] for obj in objects]
                work_q = utils.basic_queue(obj_list)

            print('Performing Delete...')
            with methods.spinner(work_q=work_q):
                utils.worker_proc(job_action=self.deleterator,
                                  num_jobs=num_files,
                                  concurrency=concurrency,
                                  t_args=payload,
                                  queue=work_q)
            utils.stupid_hack(wait=2)



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
                utils.emergency_exit('Died...')
            except KeyboardInterrupt:
                utils.emergency_exit('You killed the process...')
