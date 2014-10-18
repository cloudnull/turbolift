# =============================================================================
# Copyright [2013] [Kevin Carter]
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
import Queue
import tarfile

import prettytable

from turbolift.clouderator import actions
from turbolift import exceptions


def get_keys(obj_item):
    return obj_item.keys()


class BaseMethod(object):
    def __init__(self, job_args):
        self.job_args = job_args
        self.debug = self.job_args.get('debug', False)
        self.quiet = self.job_args.get('quiet', False)
        self.max_jobs = self.job_args.get('max_jobs')
        # Define the size at which objects are considered large.
        self.large_object_size = self.job_args.get('large_object_size')

        if self.max_jobs is None:
            self.max_jobs = 25000

        self.job = actions.CloudActions(job_args=self.job_args)

    def _encapsolate_object(self, full_path, split_path):
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
                meta['X-Object-Manifest'] = '%s/%s' % (
                    container_name,
                    link_object.lstrip(os.sep)
                )
        elif os.path.getsize(full_path) > self.large_object_size:
            manifest_path = full_path.split(split_path)[-1]
            meta['X-Object-Manifest'] = '%s/%s' % (
                container_name,
                manifest_path.lstrip(os.sep)
            )

        if self.job_args.get('save_perms'):
            obj = os.stat(full_path)
            meta['X-Object-Meta-perms'] = oct(obj.st_mode)[-4:]
            meta['X-Object-Meta-owner'] = pwd.getpwuid(obj.st_uid).pw_name
            meta['X-Object-Meta-group'] = grp.getgrgid(obj.st_gid).gr_name

        return object_item

    def _walk_directories(self, path):
        local_files = list()

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        for root_dir, _, file_names in os.walk(path):
            for file_name in file_names:
                full_path = os.path.join(root_dir, file_name)
                if full_path not in self.job_args.get('exclude'):
                    object_item = self._encapsolate_object(
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

    def print_horiz_table(self, data):
        """Print a horizontal pretty table from data."""

        # Build list of returned objects
        return_objects = list()
        fields = self.job_args.get('fields')
        if not fields:
            fields = set()
            map(fields.update, [i.keys() for i in data])

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

        print(table)

    @staticmethod
    def _process_func(func, queue):
        while True:
            try:
                func(**queue.get(timeout=.5))
            except Queue.Empty:
                break

    def _queue_generator(self, items, queue):
        deque_items = collections.deque(items)
        while deque_items:
            item_count = len(deque_items)
            if item_count < self.max_jobs:
                max_jobs = item_count
            else:
                max_jobs = self.max_jobs

            for _ in xrange(max_jobs):
                try:
                    item = deque_items.pop()
                except IndexError:
                    pass
                else:
                    queue.put(item)
            yield queue

    def _multi_processor(self, func, items):
        base_queue = multiprocessing.Queue(maxsize=self.max_jobs)
        concurrency = self.job_args.get('concurrency')

        # Yield a queue of objects with a max input as set by `max_jobs`
        for queue in self._queue_generator(items, base_queue):
            concurrent_jobs = [
                multiprocessing.Process(
                    target=self._process_func,
                    args=(func, queue,)
                ) for _ in xrange(concurrency)
            ]

            #Create an empty list to join later.
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

    @staticmethod
    def print_virt_table(data):
        """Print a vertical pretty table from data."""

        table = prettytable.PrettyTable()
        table.add_column('Keys', data.keys())
        table.add_column('Values', [str(i) for i in data.values()])
        for tbl in table.align.keys():
            table.align[tbl] = 'l'

        print(table)

    @staticmethod
    def match_filter(idx_list, pattern, dict_type=False, dict_key='name'):
        """Return Matched items in indexed files.

        :param idx_list:
        :return list
        """

        if dict_type is False:
            return [
                obj for obj in idx_list
                if re.search(pattern, obj)
            ]
        elif dict_type is True:
            return [
                obj for obj in idx_list
                if re.search(pattern, obj.get(dict_key))
            ]
        else:
            return list()

    def start(self):
        pass


def compress_files(file_list):
    """If the archive function is used, create a compressed archive.

    :param file_list:

    This function allows for multiple sources to be added to the
    compressed archive.
    """

    tmp_file = None
    try:
        # Set date and time
        date_format = '%a%b%d.%H.%M.%S.%Y'
        today = datetime.datetime.today()
        _ts = today.strftime(date_format)

        # Get Home Directory
        home_dir = os.getenv('HOME')

        # Set the name of the archive.
        set_name = ARGS.get('tar_name', '%s_%s' % ('Archive', _ts))
        file_name = '%s.tgz' % set_name

        # Set the working File.
        tmp_file = basic.jpath(root=home_dir, inode=file_name)

        # Begin creating the Archive.
        tar = tarfile.open(tmp_file, 'w:gz')
        for name in file_list:
            if basic.file_exists(name) is True:
                tar.add(name)
        tar.close()

        report.reporter(msg='ARCHIVE CREATED: %s' % tmp_file, prt=False)

        if ARGS.get('verify'):
            tar_len = tarfile.open(tmp_file, 'r')
            ver_array = []
            for member_info in tar_len.getmembers():
                ver_array.append(member_info.name)

            count = len(ver_array)
            orig_count = len(file_list)
            if orig_count != count:
                raise turbo.SystemProblem(
                    'ARCHIVE NOT VERIFIED: Archive and File List do not Match.'
                    ' Original File Count = %s, Found Archive Contents = %s'
                    % (orig_count, count)
                )
            report.reporter(
                msg='ARCHIVE CONTENTS VERIFIED: %s files' % count,
            )
    except KeyboardInterrupt:
        if basic.file_exists(tmp_file):
            basic.remove_file(tmp_file)
        turbo.emergency_exit('I have stopped at your command,'
                             ' I removed Local Copy of the Archive')
    except Exception as exp:
        if basic.file_exists(tmp_file):
            basic.remove_file(tmp_file)
            turbo.emergency_exit(
                'I am sorry i just don\'t know what you put into me, Removing'
                ' Local Copy of the Archive.'
            )
        turbo.emergency_exit(
            'Exception while working on the archive. MESSAGE: %s' % exp
        )
    else:
        return tmp_file
