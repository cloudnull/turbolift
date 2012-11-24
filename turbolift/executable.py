#!/usr/bin/env python
# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - usage        : python turbolift.local.py
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
    License Information
    
    This software has no warranty, it is provided 'as is'. It is your responsibility
    to validate the behavior of the routines and its accuracy using the code provided.
    Consult the GNU General Public license for further details (see GNU General Public License).
    
    http://www.gnu.org/licenses/gpl.html
    """

import sys
import httplib
import signal
import os
import multiprocessing
import errno
import hashlib
import tarfile
import datetime
import time
import itertools
from functools import partial
from urllib import quote

# Local Files to Import
import authentication
import arguments


def container_create(ta):
    try:
        endpoint = authdata['endpoint'].split('/')[2]
        headers = {'X-Auth-Token': authdata['token']}
        filepath = '/v1/' + authdata['tenantid'] + '/' \
            + quote(ta.container)
        conn = httplib.HTTPSConnection(endpoint, 443)
        conn.request('HEAD', filepath, headers=headers)
        resp = conn.getresponse()
        resp.read()
        if resp.status == 404:
            print '\n', 'MESSAGE\t:', resp.status, resp.reason, \
                'The Container', ta.container, 'does not Exist'
            conn.request('PUT', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()
            if resp.status >= 300:
                sys.exit('\n', 'ERROR\t:', resp.status, resp.reason, \
                    ta.container, '\n')
            print '\n', 'CREATING CONTAINER\t:', ta.container, '\n', \
                'CONTAINER STATUS\t:', resp.status, resp.reason, '\n'
        conn.close()
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', \
            sys.exc_info()[1]
        raise


def get_filenames(ta):
    directorypath = ta.source
    if os.path.isdir(directorypath) == True:
        rootdir = os.path.realpath(directorypath) + os.sep
        filelist = []
        for (root, subFolders, files) in os.walk(rootdir):
            for file in files:
                filelist.append(os.path.join(root, file))
        if ta.veryverbose:
            print '\n', rootdir, '\n'
    elif os.path.isfile(directorypath) == True:
        print 'file'
        filelist = []
        filelist.append(os.path.realpath(directorypath))
        if ta.veryverbose:
            print 'File Name\t:', filelist
    else:
        print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
        sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')
    return filelist


def compress_files(gfn):
    # create a tar archive
    print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
    home_dir = os.getenv('HOME') + os.sep
    format = '%a%b%d-%H.%M.%S.%Y.'
    today = datetime.datetime.today()
    ts = today.strftime(format)
    file_name = ts + ta.container + '.tgz'
    tmpfile = home_dir + file_name
    tar = tarfile.open(tmpfile, 'w:gz')
    for name in gfn:
        tar.add(name)
    tar.close()
    tarfile.path = tmpfile
    if ta.progress:
        print 'ARCHIVE\t:', tarfile.path
    tar_len = tarfile.open(tarfile.path, 'r')
    ver_array = []
    for member_info in tar_len.getmembers():
        ver_array.append(member_info.name)
    print 'ARCHIVE CONTENTS : %s files' % len(ver_array)
    return tarfile.path


def uploader(filename):
    global authdata
    # Put all of the  files that were found into the container
    if ta.compress or os.path.isdir(ta.source) == False:
        justfilename = filename.split(os.path.dirname(filename) + os.sep)[1]
    elif os.path.isdir(ta.source) == True:
        rootdir = os.path.realpath(ta.source) + os.sep
        justfilename = filename.split(rootdir)[1]
    try:
        retry = True
        while retry:
            retry = False
            endpoint = authdata['endpoint'].split('/')[2]
            headers = {'X-Auth-Token': authdata['token']}
            filepath = '/v1/' + authdata['tenantid'] + '/' + quote(ta.container + '/' + justfilename)
            conn = httplib.HTTPSConnection(endpoint, 443)
            if ta.upload:
                f = open(filename)
                if ta.veryverbose:
                    conn.set_debuglevel(1)
                conn.request('PUT', filepath, body=f, headers=headers)
                resp = conn.getresponse()
                resp.read()
                if ta.progress:
                    print resp.status, resp.reason, justfilename
                if resp.status == 401:
                    print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                    au = authentication.NovaAuth()
                    authdata = au.osauth(ta)
                    retry = True
                    continue
                if resp.status >= 300:
                    print 'ERROR\t:', resp.status, resp.reason, justfilename, '\n', f, '\n'
                conn.close()
                f.close()
            elif ta.tsync:
                f = open(filename)
                if ta.veryverbose:
                    conn.set_debuglevel(1)
                conn.request('HEAD', filepath, headers=headers)
                resp = conn.getresponse()
                resp.read()
                if resp.status == 404:
                    conn.request('PUT', filepath, body=f, headers=headers)
                    resp = conn.getresponse()
                    resp.read()
                    
                    if ta.progress:
                        print resp.status, resp.reason, justfilename
                    if resp.status == 401:
                        print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                        au = authentication.NovaAuth()
                        authdata = au.osauth(ta)
                        retry = True
                        continue
                    if resp.status >= 300:
                        print 'ERROR\t:', resp.status, resp.reason, justfilename, '\n', f, '\n'
                    conn.close()
                    f.close()
                else:
                    remotemd5sum = resp.getheader('etag')
                    md5 = hashlib.md5()
                    with f as fmd5:
                        for chunk in iter(lambda : fmd5.read(128
                                                             * md5.block_size), ''):
                            md5.update(chunk)
                        fmd5.close()
                    localmd5sum = md5.hexdigest()
                    if remotemd5sum != localmd5sum:
                        f = open(filename)
                        if ta.veryverbose:
                            conn.set_debuglevel(1)
                        conn.request('PUT', filepath, body=f, headers=headers)
                        resp = conn.getresponse()
                        resp.read()
                        if ta.progress:
                            print 'MESSAGE\t: CheckSumm Mis-Match', localmd5sum, '!=', remotemd5sum, '\n\t ', 'File Upload :', resp.status, resp.reason, justfilename
                        if resp.status == 401:
                            print 'MESSAGE\t: Token Seems to have expired, Forced Reauthentication is happening.'
                            au = authentication.NovaAuth()
                            authdata = au.osauth(ta)
                            retry = True
                            continue
                        if resp.status >= 300:
                            print 'ERROR\t:', resp.status, resp.reason, justfilename, '\n', f, '\n'
                        conn.close()
                        f.close()
                    else:
                        if ta.progress:
                            print 'MESSAGE\t: CheckSumm Match', localmd5sum
    except IOError, e:
        if e.errno == errno.ENOENT:
            print 'ERROR\t: path "%s" does not exist or is a broken symlink' \
                % filename
    except ValueError:
        print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' \
            % filename
    except KeyboardInterrupt, e:
        pass
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', \
            sys.exc_info()[1]
        raise


def init_worker():
    # Watch for signals
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_turbolift():
    global authdata
    global ta
    args = arguments.GetArguments()
    ta = args.get_values()
    au = authentication.NovaAuth()
    authdata = au.osauth(ta)
    try:
        if ta.rax_auth == 'MULTI':
            for region in ta.region_multi:
                print 'MESSAGE\t: Checking for Container in %s' % region
                authdata['endpoint'] = authdata[region]
                cnc = container_create(ta)
        else:
            cnc = container_create(ta)

        gfn = get_filenames(ta)
        gfn_count = len(gfn)
        print '\n', 'MESSAGE\t: "%s" files have been found.\n' % gfn_count
        
        if ta.veryverbose:
            print '\nFILELIST\t: ', gfn, '\n'
            print '\nARGS\t: ', ta, '\n', authdata
        
        print 'Beginning the Upload Process'
        if ta.cc > gfn_count:
            print 'MESSAGE\t: There are less things to do than the number of concurrent'
            print '\t  processes specified by either an override or the system defaults.'
            print '\t  I am leveling the number of concurrent processes to the number of'
            print '\t  jobs to perform.'
            multipools = gfn_count
        else:
            multipools = ta.cc
        
        windeprs = multiprocessing.freeze_support()
        pool = multiprocessing.Pool(processes=multipools, initargs=init_worker)
        if ta.veryverbose or ta.progress:
            print 'MESSAGE\t: We are going to create Processes :', multipools
        if ta.upload and ta.compress:
            if ta.rax_auth == 'MULTI':
                cf = compress_files(gfn)
                for region in ta.region_multi:
                    print 'MESSAGE\t: Uploading to %s' % region
                    authdata['endpoint'] = authdata[region]
                    cf_file = [cf]
                    result = pool.imap_unordered(uploader, cf_file)
            else:
                cf = compress_files(gfn)
                cf_file = [cf]
                result = pool.imap_unordered(uploader, cf_file)
        elif ta.upload or ta.tsync:
            if ta.rax_auth == 'MULTI':
                for region in ta.region_multi:
                    print 'MESSAGE\t: Uploading to %s' % region
                    authdata[region] = authdata[region]
                    result = pool.imap_unordered(uploader, gfn)
            else:
                result = pool.imap_unordered(uploader, gfn)
        else:
            sys.exit('FAIL\t: Some how the Application attempted to continue without the needed arguments.')
        pool.close()
        pool.join()

        if not (ta.upload or ta.tsync):
            print 'ERROR\t: Somehow I continued but I do not know how to proceed. So I Quit.'
            sys.exit('MESSAGE\t: here comes the stack trace:\n', \
                sys.exc_info()[1])
        
        print 'FINISH\t: Operation Completed, Quitting normally'
            
        if ta.compress:
            print 'MESSAGE\t: Removing Local Copy of the Archive'
            os.remove(cf)

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, terminating workers'
        pool.close()
        pool.terminate()
        if ta.compress:
            os.remove(cf)
        sys.exit('\nI have stopped at your command\n')
