#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Inforamtion

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
import errno
import hashlib
import tarfile
import datetime
import time
import itertools
from multiprocessing import Process, freeze_support, JoinableQueue
from urllib import quote

# Local Files to Import
import authentication
import arguments
import uploader


def container_create(tur_arg=None, authdata=None):
    try:
        endpoint = authdata['endpoint'].split('/')[2]
        headers = {'X-Auth-Token': authdata['token']}
        filepath = '/v1/' + authdata['tenantid'] + '/' \
            + quote(tur_arg.container)
        conn = httplib.HTTPSConnection(endpoint, 443)
        conn.request('HEAD', filepath, headers=headers)
        resp = conn.getresponse()
        resp.read()

        if resp.status == 404:
            print '\n', 'MESSAGE\t:', resp.status, resp.reason, \
                'The Container', tur_arg.container, 'does not Exist'
            conn.request('PUT', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()

            if resp.status >= 300:
                sys.exit('\n', 'ERROR\t:', resp.status, resp.reason, \
                    tur_arg.container, '\n')
            print '\n', 'CREATING CONTAINER\t:', tur_arg.container, '\n', \
                'CONTAINER STATUS\t:', resp.status, resp.reason, '\n'
        conn.close()

    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]


def get_filenames(tur_arg=None):
    filelist = []
    directorypath = tur_arg.source

    if os.path.isdir(directorypath) == True:
        rootdir = os.path.realpath(directorypath) + os.sep
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

    elif os.path.isdir(directorypath) == False:
        filelist.append(os.path.realpath(directorypath.encode('utf-8')))

        if tur_arg.debug:
            print 'File Name\t:', filelist
        return filelist
    else:
        print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
        sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')


def compress_files(tur_arg, gfn=None, sleeper=None):
    try:
        # create a tar archive
        print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
        home_dir = os.getenv('HOME') + os.sep
        format = '%a%b%d-%H.%M.%S.%Y.'
        today = datetime.datetime.today()
        ts = today.strftime(format)
        file_name = ts + tur_arg.container + '.tgz'
        
        tmp_file = home_dir + file_name
        
        tar = tarfile.open(tmp_file, 'w:gz')

        busy_chars = ['|','/','-','\\']
        for name in gfn:
            tar.add(name)

            for c in busy_chars:
                busy_char = c
                sys.stdout.write("\rCompressing - [ %s ] " % c)
                sys.stdout.flush()
                time.sleep(sleeper * .01)
        
        tar.close()

        tarfile.path = tmp_file
        if tur_arg.progress:
            print 'ARCHIVE\t:', tarfile.path
        tar_len = tarfile.open(tarfile.path, 'r')
        ver_array = []
        for member_info in tar_len.getmembers():
            ver_array.append(member_info.name)
        print 'ARCHIVE CONTENTS : %s files' % len(ver_array)
        return tarfile.path

    except:
        print 'ERROR\t: Removing Local Copy of the Archive'
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
            print 'I am sorry i just dont know what got into me', sys.exc_info()[1]
        else:
            print 'File "%tmpfile" Did not exist yet so there was nothing to delete.' % tmpfile
            print 'here some data you should read', sys.exc_info()[1]
        sys.exit('\nI have stopped at your command\n')


def queue_info(iters=None,):
    work = JoinableQueue()

    for filename in iters:
        work.put(obj=filename,)
    time.sleep(1)
    return work


def worker_proc(tur_arg=None, authdata=None, sleeper=None, multipools=None, work=None):
    for wp in range(multipools,):
        j = Process(target=uploader.UploadAction, args=(tur_arg, authdata, work,))
        j.deamon = True
        j.start()

    for i in xrange(multipools,):
        work.put(None)

def run_turbolift():
    try:
        args = arguments.GetArguments()
        tur_arg = args.get_values()
        au = authentication.NovaAuth()
        authdata = au.osauth(tur_arg)
    
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

        sleeper = float(0.01)
        container_create(tur_arg, authdata)

        if tur_arg.debug or tur_arg.progress:
            print 'MESSAGE\t: We are going to create Processes :', multipools

        if tur_arg.compress:
            cf = compress_files(tur_arg, gfn, sleeper)
            uploader.UploadAction(tur_arg, authdata, cf,)

        elif (tur_arg.upload or tur_arg.tsync):
            work = queue_info(iters,)
            worker_proc(tur_arg, authdata, sleeper, multipools, work)
        else:
            sys.exit('FAIL\t: Some how the Application attempted to continue without the needed arguments.')

        if not (tur_arg.upload or tur_arg.tsync):
            print 'ERROR\t: Somehow I continued but I do not know how to proceed. So I Quit.'
            sys.exit('MESSAGE\t: here comes the stack trace:\n', sys.exc_info()[1])
            
        if tur_arg.compress:
            print 'MESSAGE\t: Removing Local Copy of the Archive'
            if os.path.exists(cf):
                os.remove(cf)
            else:
                print 'File "cf" Did not exist so there was nothing to delete.' % cf

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, terminating workers'

    except:
        print 'Shits Broken Son...', sys.exc_info()[1]
