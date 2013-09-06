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

        LOG.info('MESSAGE\t: "%s" Files have been found.', num_files)
        LOG.debug('PAYLOAD\t: "%s"', payload)

        # Set the actions class up
        self.go = actions.cloud_actions(payload=payload)
        self.go._container_create(url=payload['url'],
                                  container=payload['c_name'])

        utils.job_processer(num_jobs=num_files,
                            objects=f_indexed,
                            job_action=self.uploaderator,
                            concur=concurrency,
                            payload=payload)

        if ARGS.get('delete_remote') is True:
            self.remote_delete(payload=payload,
                               f_indexed=f_indexed)

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
                self.go.object_putter(url=payload['url'],
                                      container=container,
                                      source=source,
                                      u_file=wfile)
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)
            except EOFError:
                utils.emergency_kill()

    def remote_delete(self, payload, f_indexed):
        """If Remote Delete was True run.

        NOTE: Remote delete will delete ALL Objects in a remote container
        which differ from the objects in the SOURCED LOCAL FILESYSTEM.

        IE: If this option is used, on one directory and then another directory
        and the files were different any difference would be deleted and based
        on the index information found in LOCAL FILE SYSTEM on the LAST
        command run.

        :return:
        """

        utils.reporter(msg='Getting file list for REMOTE DELETE')
        objects = self.go.object_lister(url=payload['url'],
                                        container=payload['c_name'])
        source = payload['source']
        obj_names = [utils.jpath(root=source,
                                 inode=obj.get('name')) for obj in objects]

        # From the remote system see if we have differences in the local system
        _objects = utils.return_diff().difference(target=f_indexed,
                                                  source=obj_names)
        if _objects:
            # Set Basic Data for file delete.
            _num_files = len(_objects)
            LOG.info('MESSAGE\t: "%s" Files have been found to be removed from'
                     ' the REMOTE CONTAINER.', _num_files)

            _concurrency = utils.set_concurrency(args=ARGS,
                                                 file_count=_num_files)

            # Delete the difference in Files.
            utils.reporter(msg='Performing Remote Delete')
            utils.job_processer(num_jobs=_num_files,
                                objects=_objects,
                                job_action=self.deleterator,
                                concur=_concurrency,
                                payload=payload)
        else:
            utils.reporter(msg='No Difference between REMOTE and LOCAL'
                               ' Directories.')

    def deleterator(self, work_q, payload):
        """Delete files to CloudFiles -Swift-.

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
                wfile = utils.get_sfile(ufile=wfile, source=payload['source'])
                self.go.object_deleter(url=payload['url'],
                                       container=payload['c_name'],
                                       u_file=wfile)
            except EOFError:
                utils.emergency_kill()
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)
