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


class UpdateRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(UpdateRunMethod, self).__init__(job_args)

    def _update(self, container, container_objects):
        if not container_objects:
            container_objects = [None]

        returned_objects = list()
        for container_object in container_objects:
            returned_objects.append(
                self.job.update_object(
                    url=self.job_args['storage_url'],
                    container=container,
                    container_object=container_object,
                    container_headers=self.job_args.get('container_headers'),
                    object_headers=self.job_args.get('object_headers')
                )
            )
        else:
            return returned_objects

    def start(self):
        indicator_options = {
            'debug': self.debug,
            'quiet': self.quiet,
            'msg': ' Updating... '
        }
        with utils.IndicatorThread(**indicator_options):
            items = self._update(
                container=self.job_args['container'],
                container_objects=self.job_args.get('object')
            )

        for item in items:
            self.print_virt_table(item.headers)
