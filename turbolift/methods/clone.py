# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import turbolift as turbo
import turbolift.utils.auth_utils as auth
import turbolift.utils.http_utils as http
import turbolift.utils.multi_utils as multi
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.clouderator import actions


class clone(object):
    """Setup and run the stream Method.

    The method will create a list of objects in a "Source" container, then
    check to see if the object exists in the target container. If it exists
    a comparison will be made between the source and target MD5 and if a
    difference is found the source object will overwrite the target. If the
    target object simply does not exists, the object will be placed in the
    target container.
    """

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Clone onjects from one container to another.

        NOTE: This method was intended for use with inter-datacenter cloning of
        objects.
        """

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('source_container'),
            source=None,
            args=ARGS
        )

        # Prep action class
        self.go = actions.CloudActions(payload=payload)

        # Ensure we have a target region.
        target_region = ARGS.get('target_region')
        if target_region is None:
            raise turbo.NoSource('No target Region was specified.')
        else:
            target_region = target_region.upper()

        # check for a target type URL
        if ARGS.get('target_snet') is True:
            target_type = 'internalURL'
        else:
            target_type = 'publicURL'

        # Format the target URL
        target_url = auth.get_surl(
            region=target_region, cf_list=payload['acfep'], lookup=target_type
        )
        if target_url is None:
            raise turbo.NoSource('No url was found from the target region')
        else:
            payload['turl'] = target_url

        # Ensure we have a target Container.
        target_container = ARGS.get('target_container')
        if target_container is None:
            raise turbo.NoSource('No target Container was specified.')
        else:
            payload['tc_name'] = target_container

        # Check if the source and target containers exist. If not Create them.
        # Source Container.
        self.go.container_create(url=payload['url'],
                                 container=payload['c_name'])
        # Target Container.
        self.go.container_create(url=target_url,
                                 container=target_container)

        report.reporter(msg='Getting Object list from the Source.')
        with multi.spinner():
            # Get a list of Objects from the Source/Target container.
            objects, list_count, last_obj = self.go.object_lister(
                url=payload['url'],
                container=payload['c_name']
            )
        if objects is None:
            raise turbo.NoSource('The source container is empty.')

        # Get the number of objects and set Concurrency
        num_files = len(objects)
        concurrency = multi.set_concurrency(args=ARGS,
                                            file_count=num_files)

        report.reporter(msg='Beginning Sync Operation.')
        kwargs = {'surl': payload['url'],
                  'turl': payload['turl'],
                  'scontainer': payload['c_name'],
                  'tcontainer': payload['tc_name'],
                  'cf_job': getattr(self.go, 'object_syncer')}

        multi.job_processer(
            num_jobs=num_files,
            objects=objects,
            job_action=multi.doerator,
            concur=concurrency,
            kwargs=kwargs
        )
