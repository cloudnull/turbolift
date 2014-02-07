# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions
from turbolift import LOG
from turbolift import methods


class Upload(object):
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
        with multi.spinner():
            f_indexed = methods.get_local_files()

        if ARGS.get('pattern_match'):
            f_indexed = basic.match_filter(
                idx_list=f_indexed, pattern=ARGS['pattern_match']
            )

        num_files = len(f_indexed)

        # Get The rate of concurrency
        concurrency = multi.set_concurrency(args=ARGS, file_count=num_files)

        # Package up the Payload
        payload = multi.manager_dict(
            http.prep_payload(
                auth=self.auth,
                container=ARGS.get('container', basic.rand_string()),
                source=basic.get_local_source(),
                args=ARGS
            )
        )

        LOG.info('MESSAGE\t: "%s" Files have been found.', num_files)
        LOG.debug('PAYLOAD\t: "%s"', payload)

        # Set the actions class up
        self.go = actions.CloudActions(payload=payload)

        kwargs = {'url': payload['url'],
                  'container': payload['c_name']}
        # get that the container exists if not create it.
        self.go.container_create(**kwargs)
        kwargs['source'] = payload['source']
        kwargs['cf_job'] = getattr(self.go, 'object_putter')

        multi.job_processer(
            num_jobs=num_files,
            objects=f_indexed,
            job_action=multi.doerator,
            concur=concurrency,
            kwargs=kwargs
        )

        if ARGS.get('delete_remote') is True:
            self.remote_delete(payload=payload,
                               f_indexed=f_indexed)

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

        report.reporter(msg='Getting file list for REMOTE DELETE')
        objects = self.go.object_lister(
            url=payload['url'], container=payload['c_name']
        )
        source = payload['source']
        obj_names = [basic.jpath(root=source, inode=obj.get('name'))
                     for obj in objects[0]]

        # From the remote system see if we have differences in the local system
        objects = multi.return_diff().difference(target=f_indexed,
                                                 source=obj_names)
        if objects:
            # Set Basic Data for file delete.
            num_files = len(objects)
            report.reporter(
                msg=('MESSAGE: "%d" Files have been found to be removed'
                     ' from the REMOTE CONTAINER.' % num_files)
            )
            concurrency = multi.set_concurrency(
                args=ARGS, file_count=num_files
            )
            # Delete the difference in Files.
            report.reporter(msg='Performing REMOTE DELETE')

            del_objects = [
                basic.get_sfile(ufile=obj, source=payload['source'])
                for obj in objects if not None
            ]
            kwargs = {'url': payload['url'],
                      'container': payload['c_name'],
                      'cf_job': getattr(self.go, 'object_deleter')}
            multi.job_processer(
                num_jobs=num_files,
                objects=del_objects,
                job_action=multi.doerator,
                concur=concurrency,
                kwargs=kwargs
            )
        else:
            report.reporter(
                msg='No Difference between REMOTE and LOCAL Directories.'
            )
