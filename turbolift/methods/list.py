# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import json

import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions


class List(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Return a list of objects from the API for a container."""

        def _check_list(list_object):
            if list_object:
                return list_object
            else:
                return None, None, None

        def _list(payload, go, last_obj):
            """Retrieve a long list of all files in a container.

            :return final_list, list_count, last_obj:
            """

            if ARGS.get('all_containers') is None:
                return _check_list(
                    list_object=go.object_lister(
                        url=payload['url'],
                        container=payload['c_name'],
                        last_obj=last_obj
                    )
                )
            else:
                return _check_list(
                    list_object=go.container_lister(
                        url=payload['url'],
                        last_obj=last_obj
                    )
                )

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('container'),
            source=None,
            args=ARGS
        )

        # Prep Actions.
        self.go = actions.CloudActions(payload=payload)

        report.reporter(
            msg='API Access for a list of Objects in %s' % payload['c_name'],
            log=True
        )
        report.reporter(
            msg='PAYLOAD : "%s"' % json.dumps(payload, indent=2),
            prt=False,
            lvl='debug',
        )

        last_obj = None
        with multi.spinner():
            objects, list_count, last_obj = _list(payload=payload,
                                                  go=self.go,
                                                  last_obj=last_obj)
            if 'pattern_match' in ARGS:
                objects = basic.match_filter(
                    idx_list=objects,
                    pattern=ARGS['pattern_match'],
                    dict_type=True
                )

            if ARGS.get('filter') is not None:
                objects = [obj for obj in objects
                           if ARGS.get('filter') in obj.get('name')]

        # Count the number of objects returned.
        if objects is False:
            report.reporter(msg='Nothing found.')
        elif ARGS.get('object_index'):
            report.reporter(
                msg=report.print_horiz_table([{'name': last_obj}]),
                log=False
            )
        elif objects is not None:
            num_files = len(objects)
            if num_files < 1:
                report.reporter(msg='Nothing found.')
            else:
                return_objects = []
                for obj in objects:
                    for item in ['hash', 'last_modified', 'content_type']:
                        if item in obj:
                            obj.pop(item)
                    return_objects.append(obj)
                report.reporter(
                    msg=report.print_horiz_table(return_objects),
                    log=False
                )
                report.reporter(msg='I found "%d" Item(s).' % num_files)
        else:
            report.reporter(msg='Nothing found.')
