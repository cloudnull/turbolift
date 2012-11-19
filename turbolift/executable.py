#!/usr/bin/python
# -*- coding: utf-8 -*-

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - usage        : python turbolift.local.py
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Inforamtion

This software has no warranty, it is provided 'as is'. It is your responsibility
to validate the behavior of the routines and its accuracy using the code provided.
Consult the GNU General Public license for further details (see GNU General Public License).
    
http://www.gnu.org/licenses/gpl.html
"""

import argparse
import sys
import json
import httplib
import signal
import os
import multiprocessing
import errno
import hashlib
import tarfile
import datetime
import time
import authentication
import itertools
from functools import partial
from urllib import quote

version = '0.2'


def containercreate(ta, authdata):
    try:
        endpoint = authdata['endpoint'].split('/')[2]
        headers = {'X-Auth-Token': authdata['token']}
        filepath = '/v1/' + authdata['tenantid'] + '/' \
            + quote(ta.container)
        conn = httplib.HTTPSConnection(endpoint, 443)
        if ta.veryverbose:
            conn.set_debuglevel(1)
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
                print '\n', 'ERROR\t:', resp.status, resp.reason, \
                    ta.container, '\n'
                exit(1)
            print '\n', 'CREATING CONTAINER\t:', ta.container, '\n', \
                'CONTAINER STATUS\t:', resp.status, resp.reason, '\n'
        conn.close()
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', \
            sys.exc_info()[1]
        raise


def get_filenames(ta):
    if ta.upload or ta.tsync:
        directorypath = ta.upload or ta.tsync
        if os.path.isdir(directorypath) == True:
            rootdir = os.path.realpath(directorypath) + os.sep
            target = os.path.realpath(rootdir)
            filelist = []
            if ta.veryverbose:
                print '\n', rootdir, '\n'

            # Locate all of the files found in the given directory

            for (root, subFolders, files) in os.walk(rootdir):
                for file in files:
                    filelist.append(os.path.join(root, file))
        else:
            print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' \
                % directorypath
            print 'MESSAGE\t: Try Again but this time with a valid directory path'
            exit(1)

    if ta.file:
        directorypath = ta.file
        if os.path.isfile(directorypath) == True:
            filelist = []
            filelist.append(os.path.realpath(directorypath))
            if ta.veryverbose:
                print 'File Name\t:', filelist
        else:
            print 'ERROR\t: file %s does not exist, or is a broken symlink' \
                % directorypath
            print 'MESSAGE\t: Try Again but this time with a valid file path'
            exit(1)
    return filelist


def compress_files(ta, gfn):
    format = '%a%b%d-%H.%M.%S.%Y.'
    today = datetime.datetime.today()
    ts = today.strftime(format)
    print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
    archivename = ts + ta.container + '.tgz'

    # create a tar archive

    tar = tarfile.open(archivename, 'w:gz')
    for name in gfn:
        tarname = os.path.realpath(name)
        tar.add(tarname)
    tar.close()
    tarfile.path = os.path.realpath(archivename)

    if ta.veryverbose:
        print 'ARCHIVE\t:', tarfile.path
    return tarfile.path


def uploader(authdata, ta, filename):
    """
    Put all of the files that were found into the container
    """

    if ta.tsync or ta.upload:
        upo = ta.tsync or ta.upload
        rootdir = os.path.realpath(upo) + os.sep
    if ta.file:
        upo = ta.file
        rootdir = os.path.realpath(upo)

    f = open(filename, 'rb')
    justfilename = filename.split(rootdir)[1]

    if ta.veryverbose:
        print '\n', f, '\n', rootdir, '\n', justfilename, '\n'

    try:
        retry = True
        while retry:
            retry = False
            endpoint = authdata['endpoint'].split('/')[2]
            headers = {'X-Auth-Token': authdata['token']}
            filepath = '/v1/' + authdata['tenantid'] + '/' \
                + quote(ta.container + '/' + justfilename)

            conn = httplib.HTTPSConnection(endpoint, 443)
            if ta.veryverbose:
                conn.set_debuglevel(1)

            if ta.upload or ta.file:
                if ta.veryverbose:
                    conn.set_debuglevel(1)
                conn.request('PUT', filepath, body=f, headers=headers)
                resp = conn.getresponse()
                resp.read()
                conn.close()
                f.close()
                if ta.progress:
                    print resp.status, resp.reason, justfilename
                if resp.status == 401:
                    print 'MESSAGE\t: Token Seems to have expired, Forced Reauthentication is happening.'
                    au = authentication.NovaAuth()
                    authdata = au.osauth(ta)
                    retry = True
                    continue

            if ta.tsync:
                conn.request('HEAD', filepath, headers=headers)
                resp = conn.getresponse()
                resp.read()
                conn.close()

                if resp.status == 404:
                    if ta.veryverbose:
                        conn.set_debuglevel(1)
                    conn.request('PUT', filepath, body=f,
                                 headers=headers)
                    resp = conn.getresponse()
                    resp.read()
                    conn.close()
                    f.close()
                    if ta.progress:
                        print resp.status, resp.reason, justfilename
                else:
                    md5 = hashlib.md5()
                    with f as fmd5:
                        for chunk in iter(lambda : fmd5.read(128
                                * md5.block_size), ''):
                            md5.update(chunk)
                        localmd5sum = md5.hexdigest()
                        remotemd5sum = resp.getheader('etag')
                        if remotemd5sum != localmd5sum:
                            if ta.veryverbose:
                                conn.set_debuglevel(1)
                            conn.request('PUT', filepath, body=fmd5,
                                    headers=headers)
                            resp = conn.getresponse()
                            resp.read()
                            conn.close()
                            fmd5.close()

                            if ta.progress:
                                print 'MESSAGE\t: CheckSumm Mis-Match', \
                                    localmd5sum, '!=', remotemd5sum, \
                                    '\n\t ', 'File Upload :', \
                                    resp.status, resp.reason, \
                                    justfilename
                        else:
                            if ta.progress:
                                print 'MESSAGE\t: CheckSumm Match', \
                                    localmd5sum

                if resp.status >= 300:
                    print 'ERROR\t:', resp.status, resp.reason, \
                        justfilename, '\n', f, '\n'
                conn.close()
    except IOError, e:
        if e.errno == errno.ENOENT:
            print 'ERROR\t: path "%s" does not exist or is a broken symlink' \
                % justfilename
    except ValueError:
        print 'ERROR\t: The data for "%s" got all jacked up, so it got skiped' \
            % justfilename
    except KeyboardInterrupt, e:
        pass
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', \
            sys.exc_info()[1]
        raise


def init_worker():
    """
    Watch for signals
    """

    signal.signal(signal.SIGINT, signal.SIG_IGN)


def get_values():
    """
    Look for flags
    """

    defaultcc = 20
    parser = argparse.ArgumentParser(formatter_class=lambda prog: \
            argparse.HelpFormatter(prog, max_help_position=50),
            usage='%(prog)s [-u] [-a | -p] [options]',
            description='Uploads lots of Files Quickly, Using the unpatented GPLv3 Cloud Files %(prog)s'
            )

    parser.add_argument('-u', '--user', nargs='?',
                        help='Defaults to env[OS_USERNAME]',
                        default=os.environ.get('OS_USERNAME', None))

    agroup = parser.add_mutually_exclusive_group()
    agroup.add_argument('-a', '--apikey', nargs='?',
                        help='Defaults to env[OS_API_KEY]',
                        default=os.environ.get('OS_API_KEY', None))
    agroup.add_argument('-p', '--password', nargs='?',
                        help='Defaults to env[OS_PASSWORD]',
                        default=os.environ.get('OS_PASSWORD', None))

    parser.add_argument(
        '-r',
        '--region',
        nargs='?',
        required=True,
        help='Defaults to env[OS_REGION_NAME]',
        default=os.environ.get('OS_REGION_NAME', None),
        )
    parser.add_argument('-c', '--container', nargs='?', required=True,
                        help='Specifies the Container')

    bgroup = parser.add_mutually_exclusive_group(required=True)
    bgroup.add_argument('-U', '--upload', nargs='?',
                        help='A local Directory to Upload')
    bgroup.add_argument('-F', '--file', nargs='?',
                        help='A local File to Upload')
    bgroup.add_argument('-T', '--tsync', nargs='?',
                        help='Sync a local Directory to Cloud Files. Similar to RSYNC'
                        )

    parser.add_argument('-I', '--internal', action='store_true',
                        help='Use Service Network')
    parser.add_argument('-P', '--progress', action='store_true',
                        help='Shows Progress While Uploading')
    parser.add_argument('-V', '--veryverbose', action='store_true',
                        help='Turn up verbosity to over 9000')

    cgroup = parser.add_mutually_exclusive_group()
    cgroup.add_argument('--compress', action='store_true',
                        help='Compress a file or directory into a single archive'
                        )
    cgroup.add_argument('--cc', nargs='?',
                        help='Container Upload Concurrency', type=int,
                        default=defaultcc)

    parser.add_argument('--url', nargs='?',
                        help='Defaults to env[OS_AUTH_URL]',
                        default=os.environ.get('OS_AUTH_URL', None))
    parser.add_argument('--version', action='version', version=version)

    args = parser.parse_args()
    args.region = args.region.upper()
    args.defaultcc = defaultcc

    if not args.user:
        print '''
No Username was provided
'''
        parser.print_help()
        exit(1)

    if not (args.apikey or args.password):
        print '''
No API Key or Password was provided
'''
        parser.print_help()
        exit(1)

    if args.tsync:
        if args.compress:
            print 'ERROR\t: You can not use compression with this function.', \
                '\n', \
                'MESSAGE\t: I have quit the application, please try again.'
            exit(1)

    if args.veryverbose:
        args.progress = True

    if args.upload or args.tsync or args.file:
        if args.cc:
            if args.cc > 150:
                print '\nMESSAGE\t: You have set the Concurency Override to', \
                    args.cc
                print '\t  This is a lot of Processes and could fork bomb your'
                print '\t  system or cause other nastyness.'
                raw_input('\t  You have been warned, Press Enter to Continue\n'
                          )

            if not args.cc == args.defaultcc:
                print 'MESSAGE\t: Setting a Concurency Override of', \
                    args.cc

        if args.compress:
            args.multipools = 1
        else:
            args.multipools = args.cc
    return args


def run_turbolift():
    ta = get_values()
    au = authentication.NovaAuth()
    authdata = au.osauth(ta)

    try:
        cnc = containercreate(ta, authdata)
        gfn = get_filenames(ta)
        gfn_count = len(gfn)
        print '\n', 'MESSAGE\t: "%s" files have been found.\n' \
            % gfn_count

        if ta.veryverbose:
            print '\nFILELIST\t: ', gfn, '\n'
            print '\nARGS\t: ', ta, '\n', authdata

        print 'Beginning the Upload Process'
        if ta.cc > gfn_count:
            print 'MESSAGE\t: There are less things to do than the number of concurent'
            print '\t  processes specified by either an orveride or the system defaults.'
            print '\t  I am leveling the number of concurent processes to the number of'
            print '\t  jobs to perform.'
            multipools = gfn_count
        else:
            multipools = ta.multipools

        manager = multiprocessing.Manager()
        q = manager.Queue()
        windeprs = multiprocessing.freeze_support()
        pool = multiprocessing.Pool(processes=multipools,
                                    initargs=(manager, init_worker))

        if ta.veryverbose or ta.progress:
            print 'MESSAGE\t: We are going to create Processes :', \
                multipools, '\n'

        if (ta.upload or ta.file) and ta.compress:
            partial_uploader = partial(uploader, authdata, ta)
            cf = compress_files(ta, gfn)
            cf_file = [cf]
            result = pool.map_async(partial_uploader, cf_file)
        elif ta.upload or ta.file or ta.tsync:
            partial_uploader = partial(uploader, authdata, ta)
            result = pool.map_async(partial_uploader, gfn)
        else:
            print 'FAIL\t: Some how the Application attempted to continue without the needed arguments.'
            exit(2)
        pool.close()
        pool.join()

        if ta.compress:
            os.remove(cf)

        if not (ta.upload or ta.file or ta.tsync):
            print 'ERROR\t: Somehow I continuted but I dont know how to proceed. So I Quit.'
            print 'MESSAGE\t: here comes the stack trace:\n', \
                sys.exc_info()[1]
            exit(1)

        print 'Operation Completed, Quitting normally'
        exit(0)
    except KeyboardInterrupt:

        print '''
Caught KeyboardInterrupt, terminating workers
'''
        pool.close()
        pool.terminate()
        if ta.compress:
            os.remove(cf)
        exit(1)


