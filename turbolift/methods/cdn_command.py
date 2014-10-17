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

    def _cdn(self):
        """Retrieve a long list of all files in a container.

        :return final_list, list_count, last_obj:
        """

        headers = dict()

        cdn_enabled = self.job_args.get('cdn_enabled')
        if cdn_enabled:
            headers['x-cdn-enabled'] = True

        cdn_disabled = self.job_args.get('cdn_disabled')
        if cdn_disabled:
            headers['x-cdn-enabled'] = False

        cdn_logs_enabled = self.job_args.get('cdn_logs_enabled')
        if cdn_logs_enabled:
            headers['x-log-retention'] = True

        cdn_logs_disabled = self.job_args.get('cdn_logs_disabled')
        if cdn_logs_disabled:
            headers['x-log-retention'] = False

        headers['x-ttl'] = self.job_args.get('cdn_ttl')

        return self.job.container_cdn_command(
            url=self.job_args['cdn_storage_url'],
            container=self.job_args['container'],
            container_object=self.job_args['object'],
            cdn_headers=headers
        )

    def start(self):
        """Return a list of objects from the API for a container."""

        with utils.IndicatorThread(debug=self.debug, quiet=self.quiet):
            cdn_item = self._cdn()

        self.print_virt_table(cdn_item.headers)
