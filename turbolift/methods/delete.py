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


class Delete(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Retrieve a long list of all files in a container."""

        def _deleterator(payload):
            """Multipass Object Delete."""

            report.reporter(msg='Getting file list')
            with multi.spinner():
                # Get all objects in a Container
                objects, list_count, last_obj = self.action(
                    url=payload['url'],
                    container=payload['c_name']
                )

                if ARGS.get('pattern_match'):
                    objects = basic.match_filter(
                        idx_list=objects,
                        pattern=ARGS['pattern_match'],
                        dict_type=True
                    )

                # Count the number of objects returned.
                if objects is False:
                    report.reporter(msg='No Container found.')
                    return
                elif objects is not None:
                    # Load the queue
                    obj_list = [obj['name'] for obj in objects]
                    num_files = len(obj_list)
                    if num_files < 1:
                        report.reporter(msg='No Objects found.')
                        return
                else:
                    report.reporter(msg='Nothing found.')
                    return

                # Get The rate of concurrency
                concurrency = multi.set_concurrency(args=ARGS,
                                                    file_count=num_files)

                if ARGS.get('object'):
                    obj_names = ARGS.get('object')
                    obj_list = [obj for obj in obj_list if obj in obj_names]
                    if not obj_list:
                        return 'Nothing Found to Delete.'
                    num_files = len(obj_list)
                report.reporter(
                    msg=('Performing Object Delete for "%s" object(s)...'
                         % num_files)
                )
                kwargs = {'url': payload['url'],
                          'container': payload['c_name'],
                          'cf_job': getattr(self.go, 'object_deleter')}
            multi.job_processer(
                num_jobs=num_files,
                objects=obj_list,
                job_action=multi.doerator,
                concur=concurrency,
                kwargs=kwargs
            )
            _deleterator(payload=payload)

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('container'),
            source=None,
            args=ARGS
        )
        report.reporter(
            msg='PAYLOAD\t: "%s"' % payload,
            log=True,
            lvl='debug',
            prt=False
        )

        self.go = actions.CloudActions(payload=payload)
        self.action = getattr(self.go, 'object_lister')

        report.reporter(
            msg='Accessing API for list of Objects in %s' % payload['c_name'],
            log=True,
            lvl='info',
            prt=True
        )

        # Delete the objects and report when done.
        _deleterator(payload=payload)

        sup_args = [ARGS.get('object'), ARGS.get('pattern_match')]
        if ARGS.get('save_container') is None and not any(sup_args):
            report.reporter(msg='Performing Container Delete.')
            with multi.spinner():
                self.go.container_deleter(url=payload['url'],
                                          container=payload['c_name'])
