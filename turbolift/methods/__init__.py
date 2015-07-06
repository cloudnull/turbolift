# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import collections
import datetime
import grp
import multiprocessing
import os
import pwd
import re
try:
    import Queue
except ImportError:
    import queue as Queue
import tarfile

import prettytable

from cloudlib import indicator
from cloudlib import logger
from cloudlib import shell
from cloudlib import utils as cloud_utils

from turbolift.clouderator import actions
from turbolift import exceptions
from turbolift import utils


LOG = logger.getLogger('turbolift')


class BaseMethod(object):
    def __init__(self, job_args):
        self.job_args = job_args
        # Define the size at which objects are considered large.
        self.large_object_size = self.job_args.get('large_object_size')

        self.max_jobs = self.job_args.get('max_jobs')
        if not self.max_jobs:
            self.max_jobs = 25000

        self.job = actions.CloudActions(job_args=self.job_args)
        self.run_indicator = self.job_args.get('run_indicator', True)
        self.indicator_options = {'run': self.run_indicator}

        self.shell = shell.ShellCommands(
            log_name='turbolift',
            debug=self.job_args['debug']
        )

        self.excludes = self.job_args.get('exclude')
        if not self.excludes:
            self.excludes = list()

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

        cnd_web_listing_enabled = self.job_args.get('cdn_web_enabled')
        if cnd_web_listing_enabled:
            headers['x-container-meta-web-listings'] = True

        cnd_web_listing_disabled = self.job_args.get('cdn_web_disabled')
        if cnd_web_listing_disabled:
            headers['x-container-meta-web-listings'] = False

        cdn_web_error_content = self.job_args.get('cdn_web_error_content')
        if cdn_web_error_content:
            headers['x-container-meta-web-error'] = cdn_web_error_content

        cdn_web_dir_type = self.job_args.get('cdn_web_dir_type')
        if cdn_web_error_content:
            headers['x-container-meta-web-directory-type'] = cdn_web_dir_type

        cdn_web_css_object = self.job_args.get('cdn_web_css_object')
        if cdn_web_css_object:
            headers['x-container-meta-web-listings-css'] = cdn_web_css_object

        cdn_web_index_object = self.job_args.get('cdn_web_index_object')
        if cdn_web_css_object:
            headers['X-Container-Meta-Web-Index'] = cdn_web_index_object

        headers['x-ttl'] = self.job_args.get('cdn_ttl')

        return self.job.container_cdn_command(
            url=self.job_args['cdn_storage_url'],
            container=self.job_args['container'],
            container_object=self.job_args['object'],
            cdn_headers=headers
        )

    def mkdir(self, path):
        self.shell.mkdir_p(path=path)

    def _delete(self, container_object=None):
        item = self.job.delete_items(
            url=self.job_args['storage_url'],
            container=self.job_args['container'],
            container_object=container_object
        )
        if item:
            LOG.debug(item.__dict__)

    def _get(self, container_object, local_object):
        self.job.get_items(
            url=self.job_args['storage_url'],
            container=self.job_args['container'],
            container_object=container_object,
            local_object=local_object
        )

    def remove_dirs(self, directory):
        """Delete a directory recursively.

        :param directory: $PATH to directory.
        :type directory: ``str``
        """

        LOG.info('Removing directory [ %s ]', directory)
        local_files = self._drectory_local_files(directory=directory)
        for file_name in local_files:
            try:
                os.remove(file_name['local_object'])
            except OSError as exp:
                LOG.error(str(exp))

        # Build a list of all local directories
        directories = sorted(
            [i for i, _, _ in os.walk(directory)],
            reverse=True
        )

        # Remove directories
        for directory_path in directories:
            try:
                os.removedirs(directory_path)
            except OSError as exp:
                if exp.errno != 2:
                    LOG.error(str(exp))
                pass

    def _drectory_local_files(self, directory):
        directory = os.path.realpath(
            os.path.expanduser(
                directory
            )
        )
        if os.path.isdir(directory):
            object_items = self._walk_directories(directory)
            return object_items
        else:
            return self._return_deque()

    def _encapsulate_object(self, full_path, split_path):
        if self.job_args.get('preserve_path'):
            container_object = full_path
        else:
            container_object = full_path.split(split_path)[-1]
            container_object = container_object.lstrip(os.sep)

        object_item = {
            'container_object': container_object,
            'local_object': full_path
        }

        container_name = self.job_args.get('container')
        meta = object_item['meta'] = dict()

        if os.path.islink(full_path):
            link_path = os.path.realpath(
                os.path.expanduser(
                    os.readlink(full_path)
                )
            )
            # When an object is a symylink the local object should be set to
            # None. This will ensure the system does not upload the "followed"
            # contents of the link.
            object_item['local_object'] = None
            link_object = link_path.split(split_path)[-1]
            meta['X-Object-Meta-symlink'] = link_path
            if link_path != link_object:
                meta['X-Object-Manifest'] = '%s%s%s' % (
                    container_name,
                    os.sep,
                    link_object.lstrip(os.sep)
                )
        elif os.path.getsize(full_path) > self.large_object_size:
            manifest_path = full_path.split(split_path)[-1]
            meta['X-Object-Manifest'] = '%s%s%s' % (
                container_name,
                os.sep,
                manifest_path.lstrip(os.sep)
            )

        if self.job_args.get('save_perms'):
            obj = os.stat(full_path)
            meta['X-Object-Meta-perms'] = oct(obj.st_mode)[-4:]
            meta['X-Object-Meta-owner'] = pwd.getpwuid(obj.st_uid).pw_name
            meta['X-Object-Meta-group'] = grp.getgrgid(obj.st_gid).gr_name

        return object_item

    def _list_contents(self, last_obj=None, single_page_return=False):
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

        objects_list = self.job.list_items(
            url=url,
            container=self.job_args['container'],
            last_obj=last_obj,
            spr=single_page_return
        )

        pattern_match = self.job_args.get('pattern_match')
        if pattern_match:
            self.match_filter(
                idx_list=objects_list,
                pattern=pattern_match,
                dict_type=True
            )

        LOG.debug('List of objects: "%s"', objects_list)
        return objects_list

    def _multi_processor(self, func, items):
        base_queue = multiprocessing.Queue(maxsize=self.max_jobs)
        concurrency = self.job_args.get('concurrency')
        item_count = len(items)
        if concurrency > item_count:
            concurrency = item_count

        # Yield a queue of objects with a max input as set by `max_jobs`
        for queue in self._queue_generator(items, base_queue):
            self.indicator_options['msg'] = 'Processing workload...'
            self.indicator_options['work_q'] = queue
            with indicator.Spinner(**self.indicator_options):
                concurrent_jobs = [
                    multiprocessing.Process(
                        target=self._process_func,
                        args=(func, queue,)
                    ) for _ in range(concurrency)
                ]

                # Create an empty list to join later.
                join_jobs = list()
                try:
                    for job in concurrent_jobs:
                        join_jobs.append(job)
                        job.start()

                    # Join finished jobs
                    for job in join_jobs:
                        job.join()
                except KeyboardInterrupt:
                    for job in join_jobs:
                        job.terminate()
                    else:
                        exceptions.emergency_kill()

    def _named_local_files(self, object_names):
        object_items = self._return_deque()
        for object_name in object_names:
            full_path = os.path.realpath(
                os.path.expanduser(
                    object_name
                )
            )

            if os.path.isfile(full_path) and full_path not in self.excludes:
                object_item = self._encapsulate_object(
                    full_path=full_path,
                    split_path=os.path.dirname(full_path)
                )
                if object_item:
                    object_items.append(object_item)
        else:
            return object_items

    @staticmethod
    def _process_func(func, queue):
        while True:
            try:
                func(**queue.get(timeout=.5))
            except Queue.Empty:
                break

    def _queue_generator(self, items, queue):
        while items:
            item_count = len(items)

            if not item_count <= self.max_jobs:
                item_count = self.max_jobs

            for _ in range(item_count):
                try:
                    queue.put(items.pop())
                except IndexError:
                    pass

            yield queue

    def _return_container_objects(self):
        """Return a list of objects to delete.

        The return tuple will indicate if it was a userd efined list of objects
        as True of False.
        The list of objects is a list of dictionaries with the key being
         "container_object".

        :returns: tuple (``bol``, ``list``)
        """

        container_objects = self.job_args.get('object')
        if container_objects:
            return True, [{'container_object': i} for i in container_objects]

        container_objects = self.job_args.get('objects_file')
        if container_objects:
            container_objects = os.path.expanduser(container_objects)
            if os.path.isfile(container_objects):
                with open(container_objects) as f:
                    return True, [
                        {'container_object': i.rstrip('\n')}
                        for i in f.readlines()
                    ]

        container_objects = self._list_contents()
        pattern_match = self.job_args.get('pattern_match')
        if pattern_match:
            container_objects = self.match_filter(
                idx_list=container_objects,
                pattern=pattern_match,
                dict_type=True,
                dict_key='name'
            )

        # Reformat list for processing
        if container_objects and isinstance(container_objects[0], dict):
            return False, self._return_deque([
                {'container_object': i['name']} for i in container_objects
            ])
        else:
            return False, self._return_deque()

    @staticmethod
    def _return_deque(deque=None, item=None):
        if not deque:
            deque = collections.deque()

        if isinstance(item, list) or isinstance(item, collections.deque):
            deque.extend(item)
        elif utils.check_basestring(item=item):
            deque.append(item)

        return deque

    def _show(self, container, container_objects):
        if self.job_args.get('cdn_info'):
            if container_objects:
                raise exceptions.SystemProblem(
                    'You can not get CDN information on an object in your'
                    ' container.'
                )
            url = self.job_args['cdn_storage_url']
        else:
            url = self.job_args['storage_url']

        if container_objects:
            returned_objects = self._return_deque()
            for container_object in container_objects:
                returned_objects.append(
                    self.job.show_details(
                        url=url,
                        container=container,
                        container_object=container_object
                    )
                )
            else:
                return returned_objects
        else:
            return [
                self.job.show_details(
                    url=url,
                    container=container
                )
            ]

    def _update(self, container, container_objects):
        if not container_objects:
            container_objects = self._return_deque()

        returned_objects = list()
        for container_object in container_objects:
            returned_objects.append(
                self.job.update_object(
                    url=self.job_args['storage_url'],
                    container=container,
                    container_object=container_object,
                    container_headers=self.job_args.get('container_headers'),
                    object_headers=self.job_args.get('object_headers')
                )
            )
        else:
            return returned_objects

    def _upload(self, meta, container_object, local_object):
        if local_object is not None and os.path.exists(local_object) is False:
            return

        item = self.job.put_object(
            url=self.job_args['storage_url'],
            container=self.job_args.get('container'),
            container_object=container_object,
            local_object=local_object,
            object_headers=self.job_args.get('object_headers'),
            meta=meta
        )
        if item:
            LOG.debug(item.__dict__)

    def _put_container(self):
        item = self.job.put_container(
            url=self.job_args['storage_url'],
            container=self.job_args.get('container')
        )
        if item:
            LOG.debug(item.__dict__)

    def _walk_directories(self, path):
        local_files = self._return_deque()

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        for root_dir, _, file_names in os.walk(path):
            for file_name in file_names:
                full_path = os.path.join(root_dir, file_name)
                if full_path not in self.excludes:
                    object_item = self._encapsulate_object(
                        full_path=full_path,
                        split_path=path
                    )
                    if object_item:
                        local_files.append(object_item)
        else:
            pattern_match = self.job_args.get('pattern_match')
            if pattern_match:
                local_files = self.match_filter(
                    idx_list=local_files,
                    pattern=pattern_match,
                    dict_type=True,
                    dict_key='container_object'
                )

            return local_files

    def _index_fs(self):
        """Returns a deque object full of local file system items.

        :returns: ``deque``
        """

        indexed_objects = self._return_deque()

        directory = self.job_args.get('directory')
        if directory:
            indexed_objects = self._return_deque(
                deque=indexed_objects,
                item=self._drectory_local_files(
                    directory=directory
                )
            )

        object_names = self.job_args.get('object')
        if object_names:
            indexed_objects = self._return_deque(
                deque=indexed_objects,
                item=self._named_local_files(
                    object_names=object_names
                )
            )

        return indexed_objects

    def _compressor(self, file_list):
        # Set the name of the archive.
        tar_name = self.job_args.get('tar_name')
        tar_name = os.path.realpath(os.path.expanduser(tar_name))
        if not os.path.isdir(os.path.dirname(tar_name)):
            raise exceptions.DirectoryFailure(
                'The path to save the archive file does not exist.'
                ' PATH: [ %s ]',
                tar_name
            )

        if not tar_name.endswith('.tgz'):
            tar_name = '%s.tgz' % tar_name

        if self.job_args.get('add_timestamp'):
            # Set date and time
            date_format = '%a%b%d.%H.%M.%S.%Y'
            today = datetime.datetime.today()
            timestamp = today.strftime(date_format)
            _tar_name = os.path.basename(tar_name)
            tar_name = os.path.join(
                os.path.dirname(tar_name), '%s-%s' % (timestamp, _tar_name)
            )

        # Begin creating the Archive.
        verify = self.job_args.get('verify')
        verify_list = self._return_deque()
        with tarfile.open(tar_name, 'w:gz') as tar:
            while file_list:
                try:
                    local_object = file_list.pop()['local_object']
                    if verify:
                        verify_list.append(local_object)
                    tar.add(local_object)
                except IndexError:
                    break

        if verify:
            with tarfile.open(tar_name, 'r') as tar:
                verified_items = self._return_deque()
                for member_info in tar.getmembers():
                    verified_items.append(member_info.name)

                if len(verified_items) != len(verify_list):
                    raise exceptions.SystemProblem(
                        'ARCHIVE NOT VERIFIED: Archive and File List do not'
                        ' Match.'
                    )

        return {
            'meta': dict(),
            'local_object': tar_name,
            'container_object': os.path.basename(tar_name)
        }

    def match_filter(self, idx_list, pattern, dict_type=False,
                     dict_key='name'):
        """Return Matched items in indexed files.

        :param idx_list:
        :return list
        """

        if dict_type is False:
            return self._return_deque([
                obj for obj in idx_list
                if re.search(pattern, obj)
            ])
        elif dict_type is True:
            return self._return_deque([
                obj for obj in idx_list
                if re.search(pattern, obj.get(dict_key))
            ])
        else:
            return self._return_deque()

    def print_horiz_table(self, data):
        """Print a horizontal pretty table from data."""

        # Build list of returned objects
        return_objects = list()
        fields = self.job_args.get('fields')
        if not fields:
            fields = set()
            for item_dict in data:
                for field_item in item_dict.keys():
                    fields.add(field_item)
            fields = sorted(fields)

        for obj in data:
            item_struct = dict()
            for item in fields:
                item_struct[item] = obj.get(item)
            else:
                return_objects.append(item_struct)

        table = prettytable.PrettyTable(fields)
        for obj in return_objects:
            table.add_row([obj.get(i) for i in fields])

        for tbl in table.align.keys():
            table.align[tbl] = 'l'

        sort_key = self.job_args.get('sort_by')
        if sort_key:
            table.sortby = sort_key

        self.printer(table)

    def print_virt_table(self, data):
        """Print a vertical pretty table from data."""

        table = prettytable.PrettyTable()
        keys = sorted(data.keys())
        table.add_column('Keys', keys)
        table.add_column('Values', [data.get(i) for i in keys])
        for tbl in table.align.keys():
            table.align[tbl] = 'l'

        self.printer(table)

    def printer(self, message, color_level='info'):
        """Print Messages and Log it.

        :param message: item to print to screen
        """

        if self.job_args.get('colorized'):
            print(cloud_utils.return_colorized(msg=message, color=color_level))
        else:
            print(message)

    def start(self):
        """This method must be overridden."""
        pass
