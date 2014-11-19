# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

from cloudlib import logger

from turbolift import exceptions
from turbolift import utils
from turbolift import methods


LOG = logger.getLogger('turbolift')


class UploadRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(UploadRunMethod, self).__init__(job_args)

    def start(self):
        indicator_options = {
            'debug': self.debug,
            'quiet': self.quiet,
            'msg': ' Uploading... '
        }

        with utils.IndicatorThread(**indicator_options):
            upload_objects = self._return_deque()
            directory = self.job_args.get('directory')
            if directory:
                upload_objects = self._return_deque(
                    deque=upload_objects,
                    item=self._drectory_local_files(
                        directory=directory
                    )
                )

            object_names = self.job_args.get('object')
            if object_names:
                upload_objects = self._return_deque(
                    deque=upload_objects,
                    item=self._named_local_files(
                        object_names=object_names
                    )
                )

            if not upload_objects:
                raise exceptions.DirectoryFailure(
                    'No objects found to process. Check your command.'
                )

            item = self.job.put_container(
                url=self.job_args['storage_url'],
                container=self.job_args.get('container')
            )
            if item:
                LOG.debug(item.__dict__)

            self._multi_processor(self._upload, items=upload_objects)
