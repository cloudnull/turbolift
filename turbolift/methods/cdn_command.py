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


class CdnRunMethod(methods.BaseMethod):
    """Setup and run the cdn Method."""

    def __init__(self, job_args):
        super(CdnRunMethod, self).__init__(job_args)

    def start(self):
        """Return a list of objects from the API for a container."""
        LOG.info('Interacting with the CDN...')
        with indicator.Spinner(run=self.run_indicator):
            cdn_item = self._cdn()

        self.print_virt_table(cdn_item.headers)
