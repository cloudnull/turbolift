# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import turbolift as clds
from turbolift.authentication import auth_utils
from turbolift.clouderator import actions
from turbolift import methods
from turbolift import utils
from turbolift.worker import ARGS


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
        payload = utils.prep_payload(
            auth=self.auth,
            container=ARGS.get('source_container'),
            source=None,
            args=ARGS
        )

        # Prep action class
        self.go = actions.cloud_actions(payload=payload)

        # Ensure we have a target region.
        target_region = ARGS.get('target_region')
        if target_region is None:
            raise clds.NoSource('No target Region was specified.')
        else:
            target_region = target_region.upper()

        # check for a target type URL
        if ARGS.get('target_snet') is True:
            target_type = 'internalURL'
        else:
            target_type = 'publicURL'

        # Format the target URL
        target_url = auth_utils.get_surl(
            region=target_region, cf_list=payload['acfep'], lookup=target_type
        )
        if target_url is None:
            raise clds.NoSource('No url was found from the target region')
        else:
            payload['turl'] = target_url

        # Ensure we have a target Container.
        target_container = ARGS.get('target_container')
        if target_container is None:
            raise clds.NoSource('No target Container was specified.')
        else:
            payload['tc_name'] = target_container

        # Check if the source and target containers exist. If not Create them.
        # Source Container.
        self.go._container_create(url=payload['url'],
                                  container=payload['c_name'])
        # Target Container.
        self.go._container_create(url=target_url,
                                  container=target_container)

        utils.reporter(msg='Getting Object list from the Source.')
        with methods.spinner():
            # Get a list of Objects from the Source/Target container.
            s_objs = self.go.object_lister(url=payload['url'],
                                           container=payload['c_name'])
        if s_objs is None:
            raise clds.NoSource('The source container is empty.')

        # TODO(kevin) make this better, or figure out a better way.
        # utils.reporter(msg='Getting Object list from the Target.')
        # with methods.spinner():
        #     # Get a list of Objects from the Source container.
        #     t_objs = self.go.object_lister(url=payload['turl'],
        #                                    container=payload['tc_name'])
        # if t_objs is not None:
        #     utils.reporter(
        #         msg=('Determining the difference between the Source and the'
        #              ' Target.')
        #     )
        #     with methods.spinner():
        #         source_objs = [obj['name'] for obj in s_objs]
        #         target_objs = [obj['name'] for obj in t_objs]
        #         tmp_objs = utils.return_diff(target=target_objs,
        #                                      source=source_objs)
        #         if tmp_objs:
        #             s_objs = [obj for obj in s_objs
        #                       if obj.get('name') in tmp_objs]
        #
        #         del t_objs, source_objs, target_objs, tmp_objs

        # Get the number of objects and set Concurrency
        num_files = len(s_objs)
        concurrency = utils.set_concurrency(args=ARGS,
                                            file_count=num_files)
        try:
            utils.reporter(msg='Loading Work Queue')
            batch_size = utils.batcher(num_files=num_files)
            for work in utils.batch_gen(data=s_objs,
                                        batch_size=batch_size,
                                        count=num_files):
                # Load returned objects into a queue
                work_q = utils.basic_queue(work)

                with methods.spinner(work_q=work_q):
                    utils.reporter(msg='Beginning Sync Operation.')
                    # Process the Queue
                    utils.worker_proc(job_action=self.syncerator,
                                      num_jobs=num_files,
                                      concurrency=concurrency,
                                      t_args=payload,
                                      queue=work_q)
        except KeyboardInterrupt:
            utils.emergency_kill(reclaim=True)

    def syncerator(self, work_q, payload):
        """Upload files to CloudFiles -Swift-.

        :param work_q:
        :param payload:
        """

        # Get work from the Queue
        while True:
            wfile = utils.get_from_q(queue=work_q)
            # If Work is None return None
            if wfile is None:
                break
            try:
                self.go.object_syncer(surl=payload['url'],
                                      turl=payload['turl'],
                                      scontainer=payload['c_name'],
                                      tcontainer=payload['tc_name'],
                                      obj=wfile)
            except EOFError:
                utils.emergency_kill()
            except KeyboardInterrupt:
                utils.emergency_kill(reclaim=True)