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

from turbolift import methods


LOG = logger.getLogger('turbolift')


class UpdateRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(UpdateRunMethod, self).__init__(job_args)

    def start(self):
        LOG.info('Updating...')
        with indicator.Spinner(**self.indicator_options):
            items = self._update(
                container=self.job_args['container'],
                container_objects=self.job_args.get('object')
            )

        for item in items:
            self.print_virt_table(item.headers)
