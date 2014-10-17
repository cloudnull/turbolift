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


class ListRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(ListRunMethod, self).__init__(job_args)

    def list_contents(self, last_obj=None):
        """Retrieve a long list of all files in a container.

        :return final_list, list_count, last_obj:
        """
        if self.job_args.get('cdn_containers'):
            if not self.job_args.get('fields'):
                self.job_args['fields'] = [
                    'name',
                    'cdn_enabled',
                    'log_retention',
                    'ttl'
                ]
            url = self.job_args['cdn_storage_url']
        else:
            url = self.job_args['storage_url']

        return self.job.list_items(
            url=url,
            container=self.job_args['container'],
            last_obj=last_obj
        )

    def start(self):
        """Return a list of objects from the API for a container."""

        with utils.IndicatorThread(debug=self.debug, quiet=self.quiet):
            objects_list = self.list_contents()
            pattern_match = self.job_args.get('pattern_match')
            if pattern_match:
                self.match_filter(
                    idx_list=objects_list,
                    pattern=self.job_args['pattern_match'],
                    dict_type=True
                )

        if objects_list:
            if isinstance(objects_list[0], dict):
                self.print_horiz_table(objects_list)
            else:
                self.print_virt_table(objects_list[0].headers)
