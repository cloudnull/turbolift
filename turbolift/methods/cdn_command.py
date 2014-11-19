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


LOG = logger.getLogger('turbolift')


class RunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(RunMethod, self).__init__(job_args)

    def start(self):
        """Return a list of objects from the API for a container."""

        with utils.IndicatorThread(debug=self.debug, quiet=self.quiet):
            cdn_item = self._cdn()

        self.print_virt_table(cdn_item.headers)
