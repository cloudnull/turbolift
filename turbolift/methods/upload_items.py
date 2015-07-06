# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

from cloudlib import logger
from cloudlib import indicator

from turbolift import exceptions
from turbolift import methods


LOG = logger.getLogger('turbolift')


class UploadRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(UploadRunMethod, self).__init__(job_args)

    def start(self):
        LOG.info('Indexing File System...')
        with indicator.Spinner(**self.indicator_options):
            upload_objects = self._index_fs()

            if not upload_objects:
                raise exceptions.DirectoryFailure(
                    'No objects found to process. Check your command.'
                )

        LOG.info('Ensuring Container...')
        with indicator.Spinner(**self.indicator_options):
            self._put_container()

        self._multi_processor(self._upload, items=upload_objects)
