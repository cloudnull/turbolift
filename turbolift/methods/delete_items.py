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

from turbolift import utils
from turbolift import methods
from turbolift.methods import list_items

LOG = logger.getLogger('turbolift')


class DeleteRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(DeleteRunMethod, self).__init__(job_args)
        # This is under the super to allow for the class object
        self._list = list_items.ListRunMethod(job_args=self.job_args)

    def _delete(self, container_object=None):
        item = self.job.delete_items(
            url=self.job_args['storage_url'],
            container=self.job_args['container'],
            container_object=container_object
        )
        if item:
            LOG.debug(item.__dict__)

    def _return_container_objects(self):
        container_objects = self._list.list_contents()

        pattern_match = self.job_args.get('pattern_match')
        if pattern_match:
            container_objects = self.match_filter(
                idx_list=container_objects,
                pattern=pattern_match,
                dict_type=True,
                dict_key='name'
            )

        # Reformat list for processing
        if container_objects and isinstance(container_objects[0], dict):
            return [{'container_object': i['name']} for i in container_objects]
        else:
            return list()

    def start(self):
        indicator_options = {
            'debug': self.debug,
            'quiet': self.quiet,
            'msg': ' Deleting... '
        }
        with utils.IndicatorThread(**indicator_options):
            # Perform the delete twice
            for _ in xrange(1):
                container_objects = self._return_container_objects()
                if container_objects:
                    self._multi_processor(
                        self._delete,
                        items=container_objects
                    )

            # Delete the container is not instructed to save it
            if not self.job_args.get('save_container'):
                self._delete()