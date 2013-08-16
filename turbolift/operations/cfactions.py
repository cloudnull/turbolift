# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import errno
import os
import sys

from turbolift.operations import exceptions
from turbolift.operations import generators
from turbolift.operations import IndicatorThread
from turbolift.operations import novacommands


class CloudFilesActions:
    """The CloudFilesActions class facilitate upload / download / delete."""

    def __init__(self, tur_arg, pay_load):
        """Prepair to run all cloudfiles actions.

        :param tur_arg:
        :param pay_load:
        """

        # Set the default Arguments
        self.container = None
        self.base_path = None
        self.oscmd = None
        self.args = tur_arg
        self.pay_load = pay_load
        self.multipools = int(self.args.get('multipools', 1))

    def job_prep(self):
        """This is a job setup function.

        The job prep will parse the payload and determine the best course of
        action
        """
        for key, val in self.pay_load:
            self.container = key
            work_q = generators.manager_queue(iters=val)
            # Prep Nova for Upload
            self.oscmd = novacommands.NovaAuth(self.args, work_q)

            if self.args.get('con_per_dir'):
                head, sep, tail = val[0].partition(key)
                self.base_path = '%s%s' % (head, sep)
            elif self.args.get('archive'):
                self.base_path = '%s%s' % (os.getenv('HOME'), os.sep)
            elif self.args.get('delete'):
                self.base_path = None
            elif self.args.get('download'):
                real_path = os.path.realpath(self.args.get('source'))
                if not os.path.isdir(real_path):
                    self.mkdir_p(real_path)
                    print('Downloaded Objects will be found here : "%s"'
                          % real_path)
                self.base_path = real_path
            elif os.path.isdir(self.args.get('source')):
                self.base_path = os.path.realpath(self.args.get('source'))
            else:
                break_down = os.path.realpath(self.args.get('source'))
                _fn = os.path.basename(break_down)
                self.base_path = break_down.strip(_fn)

            # Prep our Container
            if any([self.args.get('download'), self.args.get('delete')]):
                pass
            else:
                self.oscmd.container_create(self.container)
                if self.args.get('cdn_enabled'):
                    self.oscmd.enable_cdn(self.container)

            # If not verbose or Debug mode, show me a nice spinner
            _it = IndicatorThread(work_q=work_q)
            if not any([self.args.get('verbose'),
                        self.args.get('debug'),
                        self.args.get('os_verbose'),
                        self.args.get('quiet')]):
                thd = _it.indicator_thread()
            else:
                thd = None

            generators.worker_proc(job_action=self.run_function,
                                   multipools=self.multipools,
                                   work_q=work_q)
            if thd:
                thd.terminate()

    def run_function(self, work_q):
        """The run_function starts the threads and begins performing actions.

        have been placed into the "work_q". While the queue is not empty the
        run_function will attempt to perform actions.
        :param work_q:
        """

        while True:
            try:
                wfile = work_q.get(timeout=2)
            except Exception:
                break
            try:
                if wfile is None:
                    break

                if self.args.get('debug'):
                    print("Item = %s\n" % wfile)

                # Options that use the TSYNC Method
                if any([self.args.get('tsync'),
                        self.args.get('con_per_dir'),
                        self.args.get('upload'),
                        self.args.get('archive')]):
                    file_name = wfile.split(self.base_path)[-1].strip(os.sep)
                    if self.args.get('preserve_path'):
                        # Glue the source path back on
                        # (Do it now, as symlinks may confuse things earlier)
                        src = self.args.get('source')
                        if not src.endswith(os.sep):
                            src = "%s%s" % (src, os.sep)
                        file_name = "%s%s" % (src, file_name)
                    if self.args.get('debug'):
                        print("Destination Name = %s\n" % file_name)
                elif self.base_path is None:
                    pass
                else:
                    file_name = '%s%s%s' % (self.base_path, os.sep, wfile)
                    dir_end = wfile.split(
                        os.path.basename(wfile))[0].rstrip('/')
                    directory = '%s%s%s' % (self.base_path, os.sep, dir_end)

                # Check Options
                if any([self.args.get('upload'),
                        self.args.get('archive')]):
                    self.oscmd.put_uploader(wfile, file_name, self.container)
                elif any([self.args.get('tsync'),
                          self.args.get('con_per_dir')]):
                    self.oscmd.sync_uploader(wfile, file_name, self.container)
                elif self.args.get('download'):
                    self.mkdir_p(directory)
                    self.oscmd.get_downloader(wfile,
                                              file_name,
                                              self.container)
                elif self.args.get('delete'):
                    self.oscmd.object_deleter(wfile, self.container)
            except KeyboardInterrupt:
                sys.exit('Murdering the Workers...')
                break
            finally:
                work_q.task_done()

    def mkdir_p(self, path):
        """'mkdir -p' in Python

        Original Code came from :
        stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
        :param path:
        """

        try:
            if not os.path.isdir(path):
                os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise exceptions.DirectoryFailure(
                    'The path provided "%s" is occupied and not be used as a '
                    'directory. System was halted on Download, becaue The '
                    'provided path is a file and can not be turned into a '
                    'directory.')
