# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions


class Update(object):
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

        def _list(l_payload, go, l_last_obj):
            """Retrieve a long list of all files in a container.

            :return final_list, list_count, last_obj:
            """
            # object_lister(url, container, object_count=None, last_obj=None)
            return _check_list(
                list_object=go.object_lister(
                    url=l_payload['url'],
                    container=l_payload['c_name'],
                    last_obj=l_last_obj
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
            msg='PAYLOAD\t: "%s"' % payload,
            log=True,
            lvl='debug',
            prt=False
        )

        last_obj = None
        with multi.spinner():
            objects, list_count, last_obj = _list(
                l_payload=payload, go=self.go, l_last_obj=last_obj
            )
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
        elif len(objects) < 1:
            report.reporter(msg='Nothing found.')
        elif ARGS.get('object'):
            self.go.object_updater(
                url=payload['url'],
                container=payload['c_name'],
                u_file=last_obj
            )
        elif objects is not None:
            kwargs = {
                'url': payload['url'],
                'container': payload['c_name'],
                'cf_job': getattr(self.go, 'object_updater'),
            }

            object_names = [i['name'] for i in objects]
            num_files = len(object_names)
            concurrency = multi.set_concurrency(
                args=ARGS, file_count=num_files
            )
            multi.job_processer(
                num_jobs=num_files,
                objects=object_names,
                job_action=multi.doerator,
                concur=concurrency,
                kwargs=kwargs
            )
        else:
            report.reporter(msg='Nothing found.')
