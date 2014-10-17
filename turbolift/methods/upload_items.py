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

from cloudlib import logger

from turbolift import exceptions
from turbolift import utils
from turbolift import methods


LOG = logger.getLogger('turbolift')


class UploadRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(UploadRunMethod, self).__init__(job_args)

    def _upload(self, meta, container_object, local_object):

        if local_object is not None and os.path.exists(local_object) is False:
            return

        item = self.job.put_object(
            url=self.job_args['storage_url'],
            container=self.job_args.get('container'),
            container_object=container_object,
            local_object=local_object,
            object_headers=self.job_args.get('object_headers'),
            meta=meta
        )
        if item:
            LOG.debug(item.__dict__)

    def start(self):
        indicator_options = {
            'debug': self.debug,
            'quiet': self.quiet,
            'msg': ' Uploading... '
        }
        with utils.IndicatorThread(**indicator_options):

            upload_objects = list()

            directory = self.job_args.get('directory')
            if directory:
                directory = os.path.realpath(
                    os.path.expanduser(
                        directory
                    )
                )
                if os.path.isdir(directory):
                    object_item = self._walk_directories(directory)
                    upload_objects.extend(object_item)

            object_names = self.job_args.get('object')
            if object_names:
                for object_name in object_names:
                    full_path = os.path.realpath(
                        os.path.expanduser(
                            object_name
                        )
                    )
                    directory = os.path.dirname(full_path)

                    if os.path.isfile(full_path):
                        if full_path not in self.job_args.get('exclude'):
                            object_item = self._encapsolate_object(
                                full_path=full_path,
                                split_path=directory
                            )
                            if object_item:
                                upload_objects.append(object_item)

            if not upload_objects:
                raise exceptions.DirectoryFailure(
                    'No objects found to process. Check command and try again.'
                )

            item = self.job.put_container(
                url=self.job_args['storage_url'],
                container=self.job_args.get('container')
            )
            if item:
                LOG.debug(item.__dict__)

            self._multi_processor(self._upload, items=upload_objects)
