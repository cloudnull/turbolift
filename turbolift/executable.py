#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import sys
import httplib
import os
import operator
import tarfile
import datetime
import time
import itertools
from multiprocessing import Process, freeze_support, JoinableQueue
from urllib import quote

# Local Files to Import
from turbolift.operations import getdirsandfiles
from turbolift.operations import compressfiles
from turbolift.operations import getfilenames
from turbolift.operations import containercreate
from turbolift.operations import uploader
from turbolift.operations import authentication
from turbolift import arguments
from turbolift import info


def queue_info(iters=None,):
    """
    When the arguments "upload" or "tsync" are used all jobs will be added to the queue for processing.
    This is a simple multiprocessing queue.
    """
    work = JoinableQueue()
    for filename in iters:
        work.put(obj=filename,)
    time.sleep(1)
    return work


def worker_proc(tur_arg=None, authdata=None, multipools=None, work=None):
    """
    All threads produced by the worker are limited by the number of concurrency specified by the user.
    The Threads are all made active prior to them processing jobs.
    """
    for wp in range(multipools,):
        j = Process(target=uploader.UploadAction, args=(tur_arg, authdata, work,))
        j.deamon = True
        j.start()

    for i in xrange(multipools,):
        work.put(None)

def run_turbolift():
    """
    This is the run section of the application Turbolift.
    """
    freeze_support()
    try:
        tur_arg = arguments.GetArguments().get_values()
        authdata = authentication.NovaAuth().osauth(tur_arg)

        if tur_arg['archive']:
            containercreate.CheckAndMakeContainer(tur_arg['container'], authdata).container_create()
            cf = compressfiles.Compressor(tur_arg).compress_files()
            cfs = os.path.getsize(cf)
            print 'MESSAGE\t: Uploading... %s bytes' % cfs
            uploader.UploadAction(tur_arg, authdata, cf,)

            if tur_arg['no_cleanup']:
                print 'MESSAGE\t: Archive Location =', cf
            else:
                print 'MESSAGE\t: Removing Local Copy of the Archive'
                if os.path.exists(cf):
                    os.remove(cf)
                else:
                    print 'File "%s" Did not exist so there was nothing to delete.' % cf

        elif tur_arg['upload'] or tur_arg['tsync'] or tur_arg['con_per_dir']:
            if tur_arg['con_per_dir']:
                fd = getdirsandfiles.GetDirsAndFiles(tur_arg).get_dir_and_files()

                for fd_name in fd.keys():
                    containercreate.CheckAndMakeContainer(fd_name, authdata).container_create()
                    tur_arg['container'] = fd_name
                    gfn_count = len(fd[fd_name])
                    if tur_arg['cc'] > gfn_count:
                        multipools = gfn_count
                    else:
                        multipools = tur_arg['cc']
                    iters = itertools.chain(fd[fd_name])
                    work = queue_info(iters,)
                    worker_proc(tur_arg, authdata, multipools, work)
            else:
                containercreate.CheckAndMakeContainer(tur_arg['container'], authdata).container_create()
                gf = getfilenames.FileNames(tur_arg)
                gfn = gf.get_filenames()
                gfn_count = len(gfn)
                iters = itertools.chain(gfn)
                print '\n', 'MESSAGE\t: "%s" files have been found.\n' % gfn_count

                if tur_arg['debug']:
                    print '\nFILELIST\t: ', gfn, '\n'
                    print '\nARGS\t: ', tur_arg, '\n', authdata

                print 'Beginning the Upload Process'
                if tur_arg['cc'] > gfn_count:
                    print 'MESSAGE\t: There are less things to do than the number of concurrent'
                    print '\t  processes specified by either an override or the system defaults.'
                    print '\t  I am leveling the number of concurrent processes to the number of'
                    print '\t  jobs to perform.'
                    multipools = gfn_count
                else:
                    multipools = tur_arg['cc']

                if tur_arg['debug'] or tur_arg['verbose']:
                    print 'MESSAGE\t: We are going to create Processes :', multipools

                work = queue_info(iters,)
                worker_proc(tur_arg, authdata, multipools, work)

        else:
            sys.exit('FAIL\t: Some how the Application attempted to continue without the needed arguments.')

        if not (tur_arg['upload'] or tur_arg['tsync'] or tur_arg['archive'] or tur_arg['con_per_dir']):
            print 'ERROR\t: Somehow I continued but I do not know how to proceed. So I Quit.' \
                  'You should email me at %s' % info.__email__
            print 'MESSAGE\t: here comes the stack trace:\n'
            sys.exc_info()

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, terminating workers'


if __name__ == "__main__":
    freeze_support()
    run_turbolift()
