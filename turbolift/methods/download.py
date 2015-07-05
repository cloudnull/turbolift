# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import collections
import os

from cloudlib import logger
from cloudlib import indicator

from turbolift import methods


LOG = logger.getLogger('turbolift')


class DownloadRunMethod(methods.BaseMethod):
    """Setup and run the Download Method."""

    def __init__(self, job_args):
        super(DownloadRunMethod, self).__init__(job_args)
        self.download_items = collections.defaultdict(list)

    def _index_objects(self, objects_list):
        LOG.info('Indexing dowload objects...')

        if not self.job_args['directory'].endswith(os.sep):
            self.job_args['directory'] = '%s%s' % (
                self.job_args['directory'], os.sep
            )

        with indicator.Spinner(**self.indicator_options):
            for item in objects_list:
                normalized_name = item['name'].lstrip(os.sep)
                directory = os.path.join(
                    self.job_args['directory'].rstrip(os.sep),
                    os.path.dirname(normalized_name)
                )

                self.download_items[directory].append(
                    {
                        'container_object': item.get('name'),
                        'local_object': '%s%s' % (
                            self.job_args['directory'],
                            normalized_name
                        )
                    }
                )

    def _make_directory_structure(self):
        LOG.info('Creating local directory structure...')
        with indicator.Spinner(**self.indicator_options):
            for item in self.download_items.keys():
                self.mkdir(item)

    def start(self):
        """Return a list of objects from the API for a container."""
        LOG.info('Listing options...')
        with indicator.Spinner(**self.indicator_options):
            objects_list = self._list_contents()
            if not objects_list:
                return

        # Index items
        self._index_objects(objects_list=objects_list)
        # Create the underlying structure
        self._make_directory_structure()

        # Download everything
        LOG.debug('Download Items: %s', self.download_items)
        self._multi_processor(
            self._get,
            items=[i for i in self.download_items.values() for i in i]
        )
