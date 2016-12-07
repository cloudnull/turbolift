# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import os

from cloudlib import logger
from cloudlib import indicator

from turbolift import methods


LOG = logger.getLogger('turbolift')


class ArchiveRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(ArchiveRunMethod, self).__init__(job_args)

    def start(self):
        LOG.info('Archiving...')
        with indicator.Spinner(**self.indicator_options):
            archive = self._compressor(file_list=self._index_fs())

        LOG.info('Ensuring Container...')
        with indicator.Spinner(**self.indicator_options):
            self._put_container()

        LOG.info('Uploading Archive...')
        upload_objects = self._return_deque()
        archive_item = self._encapsulate_object(
            full_path=archive['local_object'],
            split_path=os.path.dirname(archive['local_object'])
        )
        upload_objects.append(archive_item)

        self._multi_processor(self._upload, items=upload_objects)

        if not self.job_args.get('no_cleanup'):
            os.remove(archive['local_object'])
