"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import sys
import os
import errno
import time

# Local Files to Import
from turbolift.operations import generators, novacommands


class CloudFilesActions:
    """
    The CloudFilesActions class was created to facilitate the mode of upload/
    download/delete based on file types and user Arguments.
    """
    def __init__(self, tur_arg, pay_load):
        # Set the default Arguments
        self.args = tur_arg
        self.pay_load = pay_load
        self.multipools = int(self.args['multipools'])


    def job_prep(self):
        for key,val in self.pay_load:
            self.container = key
            work_q = generators.manager_queue(iters=val)
            # Prep Nova for Upload
            self.oscmd = novacommands.NovaAuth(self.args, work_q)

            if self.args['con_per_dir'] or self.args['archive']:
                head,sep,tail = val[0].partition(key)
                self.base_path = '%s%s' % (head,sep)
            elif self.args['delete']:
                self.base_path = None
            elif self.args['download']:
                real_path = os.path.realpath(self.args['source'])
                if not os.path.isdir(real_path):
                    self.mkdir_p(real_path)
                    print('Downloaded Objects will be found here : "%s"'
                          % real_path)
                self.base_path = real_path
            elif os.path.isdir(self.args['source']):
                self.base_path = os.path.realpath(self.args['source'])
            else:
                break_down = os.path.realpath(self.args['source'])
                fn = os.path.basename(break_down)
                self.base_path = break_down.strip(fn)
            self.oscmd.connection_prep()

            # Prep our Container
            if self.args['download'] or self.args['delete']:
                pass
            else:
                self.oscmd.container_create(self.container)
                if self.args['cdn_enabled']:
                    self.oscmd.enable_cdn(self.container)

            # Thread into the job that we need to accomplish
            self.oscmd.connection_prep()
            generators.worker_proc(job_action=self.run_function,
                                   multipools=self.multipools,
                                   work_q=work_q)
    
            # Close the connection because I am done
            self.oscmd.connection_prep(conn_close=True)


    def run_function(self, work_q):
        while True:
            try:
                wfile = work_q.get()
                if wfile is None:
                    break

                if self.args['debug']:
                    print "Item = %s\n" % wfile,

                # Options that use the TSYNC Method
                sync_opts = (self.args['tsync'],
                             self.args['con_per_dir'])
                
                upload_archive = (self.args['upload'],
                                  self.args['archive'])

                if any(sync_opts) or any(upload_archive):
                    file_name = wfile.split(self.base_path)[-1].strip(os.sep)
                elif self.base_path is None:
                    pass
                else:
                    file_name = '%s%s%s' % (self.base_path, os.sep, wfile)
                    dir_end = wfile.split(os.path.basename(wfile)
                                          )[0].rstrip(os.sep)
                    directory = '%s%s%s' % (self.base_path,os.sep,dir_end)

                # Check Options
                if any(upload_archive):
                    self.oscmd.put_uploader(wfile, file_name, self.container)

                elif any(sync_opts):
                    self.oscmd.sync_uploader(wfile, file_name, self.container)
                    
                elif self.args['download']:
                    self.mkdir_p(directory)
                    self.oscmd.get_downloader(wfile,
                                              file_name,
                                              self.container)

                elif self.args['delete']:
                    self.oscmd.object_deleter(wfile, self.container)

                # If not verbose or Debug mode, show me a nice spinner
                output_types = (self.args['verbose'],
                                self.args['debug'],
                                self.args['os_verbose'],
                                self.args['quiet'])
                
                if not any(output_types):
                    busy_chars = ['|','/','-','\\']
                    for c in busy_chars:
                        # Fixes Errors with OS X due to no sem_getvalue support
                        if not sys.platform.startswith('darwin'):
                            qz = 'Number of Jobs Left [ %s ]' % work_q.qsize()
                        else:
                            qz = "OS X Can't Count... Please Wait."
                        sys.stdout.write('\rUploading Files - [ %(spin)s ] - '
                                         '%(qsize)s' % { "qsize" : qz,
                                                        "spin" : c })
                        sys.stdout.flush()
                        time.sleep(.01)

            except KeyboardInterrupt:
                sys.exit('Murdering the Workers...')
                break
            finally:
                work_q.task_done()


    def mkdir_p(self, path):
        """
        'mkdir -p' in Python
        Requires a path
        """
        # Original Code came from :
        # http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
        try:
            if not os.path.isdir(path):
                os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                print('The path provided "%s" is occupied and not be used as a '
                      'directory System was halted on Download, becaue The '
                      'provided path is a file and can not be turned into a '
                      'directory.')
                raise