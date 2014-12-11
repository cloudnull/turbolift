# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import os

from cloudlib import logger
from cloudlib import indicator

from turbolift import methods


LOG = logger.getLogger('turbolift')


class DownloadRunMethod(methods.BaseMethod):
    """Setup and run the Download Method."""

    def __init__(self, job_args):
        super(DownloadRunMethod, self).__init__(job_args)

    def start(self):
        """Return a download of objects from the API for a container."""

        self.indicator_options['msg'] = 'Building object index... '
        with indicator.Spinner(**self.indicator_options):
            objects_list = self._list_contents()

        if objects_list:
            directories = set()
            for item in objects_list:
                directories.add(os.path.basename(item.get('name')))









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

from turbolift.logger import logger


LOG = logger.getLogger('turbolift')


class Download(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Retrieve a long list of all files in a container."""

        # Package up the Payload
        payload = http.prep_payload(
            auth=self.auth,
            container=ARGS.get('container'),
            source=ARGS.get('source'),
            args=ARGS
        )
        self.go = actions.CloudActions(payload=payload)
        self.action = getattr(self.go, 'object_lister')

        LOG.info('Attempting Download of Remote path %s', payload['c_name'])

        if ARGS.get('verbose'):
            LOG.info(
                'Accessing API for a list of Objects in %s', payload['c_name']
            )

        report.reporter(
            msg='PAYLOAD : [ %s ]' % payload,
            prt=False,
            lvl='debug',
        )

        report.reporter(msg='getting file list')
        with multi.spinner():
            # Get all objects in a Container
            objects, list_count, last_obj = self.action(
                url=payload['url'],
                container=payload['c_name'],
                last_obj=ARGS.get('index_from')
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
                num_files = len(objects)
                if num_files < 1:
                    report.reporter(msg='No Objects found.')
                    return
            else:
                report.reporter(msg='No Objects found.')
                return

            # Get The rate of concurrency
            concurrency = multi.set_concurrency(args=ARGS,
                                                file_count=num_files)
            # Load the queue
            obj_list = [obj['name'] for obj in objects if obj.get('name')]

        report.reporter(msg='Building Directory Structure.')
        with multi.spinner():
            if ARGS.get('object'):
                obj_names = ARGS.get('object')
                obj_list = [obj for obj in obj_list if obj in obj_names]
                num_files = len(obj_list)
            elif ARGS.get('dir'):
                objpath = ARGS.get('dir')
                obj_list = [obj for obj in obj_list if obj.startswith(objpath)]
                num_files = len(obj_list)

            # from objects found set a unique list of directories
            unique_dirs = basic.set_unique_dirs(object_list=obj_list,
                                                root_dir=payload['source'])
            for udir in unique_dirs:
                basic.mkdir_p(path=udir)

        kwargs = {'url': payload['url'],
                  'container': payload['c_name'],
                  'source': payload['source'],
                  'cf_job': getattr(self.go, 'object_downloader')}

        report.reporter(msg='Performing Object Download.')
        multi.job_processer(
            num_jobs=num_files,
            objects=obj_list,
            job_action=multi.doerator,
            concur=concurrency,
            kwargs=kwargs
        )
        if ARGS.get('max_jobs') is not None:
            report.reporter(
                msg=('This is the last object downloaded. [ %s ]'
                     % last_obj),
                log=True
            )
