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


class download(object):
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
            source=ARGS.get('source'),
            args=ARGS
        )
        self.go = actions.cloud_actions(payload=payload)
        self.action = getattr(self.go, 'object_lister')

        LOG.info('Attempting Download of Remote path %s', payload['c_name'])

        if ARGS.get('verbose'):
            LOG.info(
                'Accessing API for a list of Objects in %s', payload['c_name']
            )

        if ARGS.get('debug'):
            LOG.debug('PAYLOAD\t: "%s"', payload)

        utils.reporter(msg='getting file list')
        with methods.spinner():
            # Get all objects in a Container
            objects = self.action(url=payload['url'],
                                  container=payload['c_name'])

            # Count the number of objects returned.
            if objects is False:
                utils.reporter(msg='No Container found.')
                return
            elif objects is not None:
                num_files = len(objects)
                if num_files < 1:
                    utils.reporter(msg='No Objects found.')
                    return
            else:
                utils.reporter(msg='No Objects found.')
                return

            # Get The rate of concurrency
            concurrency = utils.set_concurrency(args=ARGS,
                                                file_count=num_files)
            # Load the queue
            obj_list = [obj['name'] for obj in objects]
            work_q = utils.basic_queue(obj_list)

        utils.reporter(msg='Building Directory Structure.')
        with methods.spinner():
            unique_dirs = []
            for obj in obj_list:
                full_path = os.path.join(payload['source'], obj)
                dir_path = full_path.split(
                    os.path.basename(full_path)
                )[0].rstrip(os.sep)
                unique_dirs.append(dir_path)

            for udir in  set(unique_dirs):
                utils.mkdir_p(path=udir)

        utils.reporter(msg='Performing Object Download...')
        with methods.spinner(work_q=work_q):
            utils.worker_proc(job_action=self.downloaderator,
                              num_jobs=num_files,
                              concurrency=concurrency,
                              t_args=payload,
                              queue=work_q)

    def downloaderator(self, work_q, payload):
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
                self.go.object_downloader(url=payload['url'],
                                          container=payload['c_name'],
                                          source=payload['source'],
                                          u_file=wfile)
            except EOFError:
                utils.emergency_kill()
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)
