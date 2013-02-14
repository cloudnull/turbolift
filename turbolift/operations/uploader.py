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


class UploadAction:
    """
    The UploadAction class was created to facilitate the mode of upload based on file types and user Arguments.
    """
    def __init__(self, tur_arg, pay_load):
        # Set the default Arguments
        self.args = tur_arg
        self.pay_load = pay_load
        self.multipools = int(self.args['multipools'])


    def job_prep(self):
        # Prep Nova for Upload
        self.oscmd = novacommands.NovaAuth(self.args)

        for key,val in self.pay_load:
            self.container = key
            work_q = generators.manager_queue(iters=val)

            if self.args['con_per_dir'] or self.args['archive']:
                head,sep,tail = val[0].partition(key)
                self.base_path = '%s%s' % (head,sep)
            elif os.path.isdir(self.args['source']):
                self.base_path = os.path.realpath(self.args['source'])
            else:
                break_down = os.path.realpath(self.args['source'])
                fn = os.path.basename(break_down)
                self.base_path = break_down.strip(fn)

            # Prep our Container
            self.oscmd.connection_prep()
            self.oscmd.container_create(self.container)
            if self.args['cdn_enabled']:
                self.oscmd.enable_cdn(self.container)
                sys.exit()
    
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

                file_name = wfile.split(self.base_path)[-1].strip(os.sep)

                # Options that use the TSYNC Method
                sync_opts = (self.args['tsync'],
                             self.args['con_per_dir'])

                # Check Options
                if self.args['upload'] or self.args['archive']:
                    self.oscmd.put_uploader(wfile, file_name, self.container)

                elif any(sync_opts):
                    self.oscmd.sync_uploader(wfile, file_name, self.container)

                # If not verbose or Debug mode, show me a nice spinner
                output_types = (self.args['verbose'],
                                self.args['debug'],
                                self.args['os_verbose'])
                
                if not any(output_types):
                    busy_chars = ['|','/','-','\\']
                    for c in busy_chars:
                        # Fixes Errors with OS X due to no sem_getvalue support
                        if not sys.platform.startswith('darwin'):
                            qz = 'Number of Jobs Left [ %s ]' % self.filename.qsize()
                        else:
                            qz = "OS X Can't Count... Please Wait."
                        sys.stdout.write('\rUploading Files - [ %(spin)s ] - %(qsize)s' % { "qsize" : qz, "spin" : c })
                        sys.stdout.flush()
                        time.sleep(.01)

            except KeyboardInterrupt:
                sys.exit('Murdering the Workers...')
                break
            finally:
                work_q.task_done()

