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
from turbolift import authentication
from turbolift import arguments
from turbolift import uploader
from turbolift import info


#noinspection PyBroadException
def container_create(container, authdata):
    """
    Create a container if the container specified on the command line did not already exist.
    """
    try:
        endpoint = authdata['endpoint'].split('/')[2]
        headers = {'X-Auth-Token': authdata['token']}
        filepath = '/v1/%s/%s' % (authdata['tenantid'], quote(container))
        conn = httplib.HTTPSConnection(endpoint, 443)
        conn.request('HEAD', filepath, headers=headers)
        resp = conn.getresponse()
        resp.read()
        status_codes = (resp.status, resp.reason, container)

        if resp.status == 404:
            print '\nMESSAGE\t: %s %s The Container "%s" does not Exist' % status_codes
            conn.request('PUT', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()

            if resp.status >= 300:
                print '\nERROR\t: %s %s "%s"\n' % status_codes
                sys.exc_info()
            print '\nCREATING CONTAINER\t: "%s"\nCONTAINER STATUS\t: %s %s' % status_codes
        conn.close()

    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]


def get_dir_and_files(tur_arg=None):
    """
    Find all files and folders in all directories, this creates a Dictionary for all directories with a list
    for all of the files found in all of the directories.
    """
    dname = []
    cpd = {}
    if not tur_arg.source.endswith(os.sep):
        directorypath = '%s%s' % (tur_arg.source, os.sep)
    else:
        directorypath = tur_arg.source

    for (root, directory, file) in os.walk(directorypath, topdown=True, onerror=None, followlinks=False):
        dname.append(root)

    for dir in dname:
        fs = []
        for fname in os.listdir(dir):
            if os.path.isfile('%s/%s' % (dir, fname)) is True:
                if fname is not None:
                    fs.append('%s%s%s' % (dir, os.sep, fname))

                get_file_size = [ [files, os.path.getsize(files)] for files in fs ]
                sort_size = sorted(get_file_size, key=operator.itemgetter(1), reverse=True)
                flist = []

                for file_name, size in sort_size:
                    flist.append(os.path.normpath(file_name))

        if flist:
            cpd[ os.path.basename(dir) ] = flist

    base_dir = os.path.basename(directorypath.rstrip(os.sep))
    cpd[base_dir] = cpd['']
    del cpd['']
    return cpd


def get_filenames(tur_arg=None):
    """
    Find all files specified in the "source" path, then create a list for all of files using the full path.
    """
    filelist = []
    directorypath = tur_arg.source

    if os.path.isdir(directorypath):
        rootdir = '%s%s' % (os.path.realpath(directorypath), os.sep)
        for (root, subfolders, files) in os.walk(rootdir.encode('utf-8')):
            for file in files:
                filelist.append(os.path.join(root.encode('utf-8'), file.encode('utf-8')))

        if tur_arg.debug:
            print '\n', rootdir, '\n'

        get_file_size = [ [files, os.path.getsize(files)] for files in filelist ]
        sort_size = sorted(get_file_size, key=operator.itemgetter(1))
        files = []

        for file_name, size in reversed(sort_size):
            files.append(file_name)
        return files

    elif not os.path.isdir(directorypath):
        filelist.append(os.path.realpath(directorypath.encode('utf-8')))

        if tur_arg.debug:
            print 'File Name\t:', filelist
        return filelist
    else:
        print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
        sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')


#noinspection PyBroadException
def compress_files(tur_arg, sleeper=None):
    """
    If the archive function is used, create a compressed archive from all of files found from the "source" argument.
    This function allows for multiple sources to be added to the compressed archive.
    """
    global tmp_file
    try:
        filelist = []

        for long_file_list in tur_arg.source:
            directorypath = long_file_list

            if os.path.isdir(directorypath):
                rootdir = '%s%s' % (os.path.realpath(directorypath), os.sep)
                for (root, subfolders, files) in os.walk(rootdir.encode('utf-8')):
                    for file in files:
                        filelist.append(os.path.join(root.encode('utf-8'), file.encode('utf-8')))

            elif not os.path.isdir(directorypath):
                filelist.append(os.path.realpath(directorypath.encode('utf-8')))

            else:
                print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
                sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')

        if tur_arg.debug:
            print '\n', filelist, '\n', tur_arg.source, '\n'

        # create a tar archive
        print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
        format = '%a%b%d-%H.%M.%S.%Y.'
        today = datetime.datetime.today()
        ts = today.strftime(format)

        if tur_arg.tar_name:
            tmp_file = '%s%s.tgz' % (ts, tur_arg.tar_name)
        else:
            home_dir = '%s%s' % (os.getenv('HOME'), os.sep)
            file_name = '%s%s.tgz' % (ts, tur_arg.container)
            tmp_file = '%s%s' % (home_dir, file_name)

        tar = tarfile.open(tmp_file, 'w:gz')

        busy_chars = ['|','/','-','\\']
        for name in filelist:
            tar.add(name)

            for c in busy_chars:
                sys.stdout.write("\rCompressing - [ %s ] " % c)
                sys.stdout.flush()
                time.sleep(sleeper * .01)

        tar.close()

        tarfile.path = tmp_file
        if tur_arg.verbose:
            print 'ARCHIVE\t:', tarfile.path
        tar_len = tarfile.open(tarfile.path, 'r')
        ver_array = []
        for member_info in tar_len.getmembers():
            ver_array.append(member_info.name)
        print 'ARCHIVE CONTENTS : %s files' % len(ver_array)
        return tarfile.path

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, terminating workers'
        print 'MESSAGE\t: Removing Local Copy of the Archive'
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        sys.exit('\nI have stopped at your command\n')
    except:
        print 'ERROR\t: Removing Local Copy of the Archive'
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
            print 'I am sorry i just don\'t know what you put into me Maybe this helps :\n', sys.exc_info()[1]
        else:
            print 'File "%s" Did not exist yet so there was nothing to delete.' % tmpfile
            print 'here some data you should read', sys.exc_info()[1]



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
    try:
        tur_arg = arguments.GetArguments().get_values()
        authdata = authentication.NovaAuth().osauth(tur_arg)
    
        sleeper = float(0.01)

        if tur_arg.archive:
            container_create(tur_arg.container, authdata)
            cf = compress_files(tur_arg, sleeper)
            cfs = os.path.getsize(cf)
            print 'MESSAGE\t: Uploading... %s bytes' % cfs
            uploader.UploadAction(tur_arg, authdata, cf,)

            if tur_arg.no_cleanup:
                print 'MESSAGE\t: Archive Location =', cf
            else:
                print 'MESSAGE\t: Removing Local Copy of the Archive'
                if os.path.exists(cf):
                    os.remove(cf)
                else:
                    print 'File "%s" Did not exist so there was nothing to delete.' % cf

        elif tur_arg.upload or tur_arg.tsync or tur_arg.con_per_dir:
            if tur_arg.con_per_dir:
                fd = get_dir_and_files(tur_arg)

                for fd_name in fd.keys():
                    container_create(fd_name, authdata)
                    tur_arg.container = fd_name
                    gfn_count = len(fd[fd_name])
                    if tur_arg.cc > gfn_count:
                        multipools = gfn_count
                    else:
                        multipools = tur_arg.cc
                    iters = itertools.chain(fd[fd_name])
                    work = queue_info(iters,)
                    worker_proc(tur_arg, authdata, multipools, work)
            else:
                container_create(tur_arg.container, authdata)
                gfn = get_filenames(tur_arg)
                gfn_count = len(gfn)
                iters = itertools.chain(gfn)
                print '\n', 'MESSAGE\t: "%s" files have been found.\n' % gfn_count

                if tur_arg.debug:
                    print '\nFILELIST\t: ', gfn, '\n'
                    print '\nARGS\t: ', tur_arg, '\n', authdata

                print 'Beginning the Upload Process'
                if tur_arg.cc > gfn_count:
                    print 'MESSAGE\t: There are less things to do than the number of concurrent'
                    print '\t  processes specified by either an override or the system defaults.'
                    print '\t  I am leveling the number of concurrent processes to the number of'
                    print '\t  jobs to perform.'
                    multipools = gfn_count
                else:
                    multipools = tur_arg.cc

                if tur_arg.debug or tur_arg.verbose:
                    print 'MESSAGE\t: We are going to create Processes :', multipools

                work = queue_info(iters,)
                worker_proc(tur_arg, authdata, multipools, work)

        else:
            sys.exit('FAIL\t: Some how the Application attempted to continue without the needed arguments.')

        if not (tur_arg.upload or tur_arg.tsync or tur_arg.archive or tur_arg.con_per_dir):
            print 'ERROR\t: Somehow I continued but I do not know how to proceed. So I Quit.' \
                  'You should email me at %s' % info.__email__
            print 'MESSAGE\t: here comes the stack trace:\n'
            sys.exc_info()

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, terminating workers'


if __name__ == "__main__":
    freeze_support()
    run_turbolift()
