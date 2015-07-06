# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import os
import tempfile

from cloudlib import logger
from cloudlib import indicator

from turbolift.authentication import auth
from turbolift import methods
from turbolift import utils
import turbolift

LOG = logger.getLogger('turbolift')


class CloneRunMethod(methods.BaseMethod):
    """Setup and run the clone method."""

    def __init__(self, job_args):
        super(CloneRunMethod, self).__init__(job_args)
        #  TODO(cloudnull) Remove this in future releases
        source_container = self.job_args.get('source_container')
        if source_container:
            LOG.warn(
                'The use of the ``--source-container`` flag has been'
                ' deprecated and will be removed in future releases. Please'
                ' use the ``--container`` flag instead.'
            )
            self.job_args['container'] = self.job_args['source_container']

        self.target_args = self.job_args.copy()
        self.target_process = None

    def _target_auth(self):
        self.target_args['container'] = self.job_args['target_container']
        self.target_args['os_region'] = self.job_args['target_region']

        # Set the target auth url
        target_auth_url = self.job_args.get('target_auth_url')
        if target_auth_url:
            self.target_args['os_auth_url'] = target_auth_url

        # Set the target user
        target_user = self.job_args.get('target_user')
        if target_user:
            self.target_args['os_user'] = target_user

        # Set the target password
        target_password = self.job_args.get('target_password')
        if target_password:
            self.target_args['os_password'] = target_password

        # Set the target apikey
        target_apikey = self.job_args.get('target_apikey')
        if target_apikey:
            self.target_args['os_apikey'] = target_apikey

        # Disable any active auth plugins, This is done because all information
        #  that may be needed from the plugin is already loaded.
        auth_plugin_list = turbolift.auth_plugins(
            auth_plugins=self.job_args.get('auth_plugins')
        )
        for item in auth_plugin_list.keys():
            self.target_args[item] = None

        # Authenticate to the target region
        LOG.info('Authenticating against the target')
        self.target_args.update(
            auth.authenticate(
                job_args=self.target_args
            )
        )

    def _clone(self, container_object, object_headers):
        local_temp_object = os.path.join(
            self.job_args['clone_workspace'],
            container_object
        )
        try:
            self.job.get_items(
                url=self.job_args['storage_url'],
                container=self.job_args['container'],
                container_object=container_object,
                local_object=local_temp_object
            )
            self.job.put_object(
                url=self.target_args['storage_url'],
                container=self.target_args['container'],
                container_object=container_object,
                local_object=local_temp_object,
                object_headers=object_headers
            )
        finally:
            if os.path.isfile(local_temp_object):
                os.remove(local_temp_object)

    def _check_clone(self, *args, **kwargs):
        resp = self.job.show_details(
            url=self.target_args['storage_url'],
            container=self.target_args['container'],
            container_object=kwargs['name']
        )

        check_hashes = resp.headers.get('etag') == kwargs['hash']
        if resp.status_code == 404 or not check_hashes:
            self._clone(
                container_object=kwargs['name'],
                object_headers=resp.headers
            )
        else:
            LOG.debug(
                'Nothing cloned. Object "%s" is the same in both regions,'
                ' [ %s ] and [ %s ]',
                kwargs['name'],
                self.target_args['os_region'],
                self.job_args['os_region']
            )

    def _clone_worker(self, objects_list):
        log_msg = self.indicator_options['msg'] = 'Ensuring Target Container'
        LOG.info(log_msg)
        with indicator.Spinner(**self.indicator_options):
            self.job.put_container(
                url=self.target_args['storage_url'],
                container=self.target_args['container']
            )

        log_msg = self.indicator_options['msg'] = 'Creating workspace'
        LOG.info(log_msg)
        with indicator.Spinner(**self.indicator_options):
            workspace = self.job_args['clone_workspace'] = tempfile.mkdtemp(
                suffix='_clone',
                prefix='turbolift_',
                dir=self.job_args.get('workspace')
            )
            working_dirs = set(
                [os.path.dirname(i['name']) for i in objects_list]
            )
        for item in working_dirs:
            self.mkdir(
                path=os.path.join(
                    self.job_args['clone_workspace'],
                    item
                )
            )

        LOG.info('Running Clone')
        try:
            self._multi_processor(self._check_clone, items=objects_list)
        finally:
            self.remove_dirs(workspace)

    def start(self):
        """Clone objects from one container to another.

        This method was built to clone a container between data-centers while
        using the same credentials. The method assumes that an authentication
        token will be valid within the two data centers.
        """

        LOG.info('Clone warm up...')
        # Create the target args
        self._target_auth()

        last_list_obj = None
        while True:
            self.indicator_options['msg'] = 'Gathering object list'
            with indicator.Spinner(**self.indicator_options):
                objects_list = self._list_contents(
                    single_page_return=True,
                    last_obj=last_list_obj
                )
                if not objects_list:
                    return

            last_obj = utils.byte_encode(objects_list[-1].get('name'))
            LOG.info(
                'Last object [ %s ] Last object in the list [ %s ]',
                last_obj,
                last_list_obj
            )
            if last_list_obj == last_obj:
                return
            else:
                last_list_obj = last_obj
                self._clone_worker(objects_list=objects_list)
