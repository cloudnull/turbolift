# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import hashlib

from cloudlib import logger

from turbolift import utils
from turbolift import methods


LOG = logger.getLogger('turbolift')


class ListRunMethod(methods.BaseMethod):
    """Setup and run the list Method."""

    def __init__(self, job_args):
        super(ListRunMethod, self).__init__(job_args)

    def start(self):
        """Return a list of objects from the API for a container."""

        with utils.IndicatorThread(debug=self.debug, quiet=self.quiet):
            objects_list = self._list_contents()
            pattern_match = self.job_args.get('pattern_match')
            if pattern_match:
                self.match_filter(
                    idx_list=objects_list,
                    pattern=self.job_args['pattern_match'],
                    dict_type=True
                )

        if objects_list:
            if isinstance(objects_list[0], dict):
                filter_dlo = self.job_args.get('filter_dlo')
                if filter_dlo:
                    dynamic_hash = hashlib.sha256(
                        self.job_args.get('container')
                    )
                    dynamic_hash = dynamic_hash.hexdigest()
                    objects_list = [
                        i for i in objects_list
                        if dynamic_hash not in i.get('name')
                    ]
                string_filter = self.job_args.get('filter')
                if string_filter:
                    objects_list = [
                        i for i in objects_list
                        if string_filter in i.get('name')
                    ]
                self.print_horiz_table(objects_list)
            else:
                self.print_virt_table(objects_list[0].headers)
