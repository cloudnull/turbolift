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
import errno
import hashlib
import time
from multiprocessing import JoinableQueue
from urllib import quote

# Local Files to Import
import authentication


class UploadAction:
    """
    The UploadAction class was created to facilitate the mode of upload based on file types and user Arguments.
    """
    def __init__(self, tur_arg, authdata, filename):
        self.ad = authdata
        self.args = tur_arg
        self.error = 0
        self.open_conn()
        self.filename = filename

        if self.args['archive'] or os.path.isfile(self.args['source']) == True:
            path = os.path.realpath(self.args['source'])
            self.filename = self.args['source'].split(os.sep)[-1]
            self.just_filename = self.filename

            self.put_uploader(self.filename)
            if self.args['debug']:
                print 'filename =', self.filename

        else:
            while True:
                #noinspection PyBroadException
                try:
                    self.wfile = self.filename.get()
                    if self.wfile is None:
                        # Poison pill means shutdown
                        break
                    if self.args['debug']:
                        print "Item =", self.wfile, 
                    path = os.path.realpath(self.args['source'])
                    self.just_filename = self.wfile.split(path)[-1].strip(os.sep)
                    
                    if self.args['con_per_dir']:
                        self.just_filename = os.path.basename(self.just_filename)

                    if self.args['upload']:
                        self.put_uploader(self.wfile,)
                    elif self.args['tsync'] or self.args['con_per_dir']:
                        self.sync_uploader(self.wfile,)
                    else:
                        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]

                    if not (self.args['verbose'] or self.args['debug']):
                        busy_chars = ['|','/','-','\\']
                        for c in busy_chars:
                            # Fixes Errors with OS X due to no sem_getvalue support
                            if not sys.platform == 'darwin':
                                qz = self.filename.qsize()
                            else:
                                qz = "OS X Can't Count... Please Wait."
                            sys.stdout.write("\rUploading Files - [ %(spin)s ] - Work Load %(qsize)s "
                                             % { "qsize" : qz, "spin" : c })
                            sys.stdout.flush()
                            time.sleep(.1)
                    self.filename.task_done()

                except KeyboardInterrupt:
                    print 'Murdering the Workers...'
                    break

                except:
                    print 'Failure', sys.exc_info()[1]
                    break

            self.conn.close()


    def re_auth(self):
        """
        Created to re-run and store authentication information upon error
        """
        self.ad = authentication.NovaAuth().osauth(self.args)
        return self


    def open_conn(self):
        """
        Opens the initial connection to the Swift repository from within the UploadAction class.
        Also used to re-open a connection on error
        """
        time.sleep(1)
        endpoint = self.ad['endpoint'].split('/')[2]
        self.headers = {'Connection:' : 'Keep-alive', 'X-Auth-Token': self.ad['token']}
        self.conn = httplib.HTTPSConnection(endpoint, 443)
        if self.args['debug']:
            self.conn.set_debuglevel(1)
        return self


    def put_uploader(self, filename,):
        """
        This is the simple upload Method. There is no file level checking at the target.
        The files are simply uploaded.
        """
        try:
            up_retry = True
            while up_retry:
                up_retry = False
                if self.error >= 5:
                    print 'ERROR\t: The Application attempted to retry too many times.'
                    print 'ERROR\t: Retry attempts were %s' % self.error
                    break

                quoted_list = [ 'v1', self.ad['tenantid'], self.args['container'], self.just_filename ]
                filepath = '/%s' % quote('/'.join(quoted_list))
                
                f = open(filename, 'rb')
                if self.args['debug']:
                    print 'MESSAGE\t: Upload path =', filepath
                    self.conn.set_debuglevel(1)

                self.conn.request('PUT', filepath, body=f, headers=self.headers)

                resp = self.conn.getresponse()
                resp.read()
                f.close()

                if self.args['verbose'] or self.args['debug']:
                    print 'info', resp.status, resp.reason, self.just_filename

                if resp.status is None:
                    UploadAction.open_conn(self)
                    UploadAction.re_auth(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status == 401:
                    print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                    UploadAction.re_auth(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status == 400:
                    print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                    UploadAction.open_conn(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status >= 300:
                    print 'ERROR\t:', resp.status, resp.reason, self.just_filename, '\n', f, '\n'

        except IOError:
            print 'ERROR\t: path "%s" does not exist or is a broken symlink' % filename
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % filename
        except KeyboardInterrupt:
            pass


    def sync_uploader(self, filename):
        """
        This is the Sync method which uploads files to the swift repository if they are not already found.
        If a file "name" is found locally and in the swift repository an MD5 comparison is done between the two files.
        If the MD5 is miss-matched the local file is uploaded to the repository.
        """
        #noinspection PyBroadException
        try:
            up_retry = True
            while up_retry:
                up_retry = False
                if self.error >= 5:
                    print 'ERROR\t: The Application attempted to retry too many times.'
                    print 'ERROR\t: Retry attempts were %s' % self.error
                    break

                quoted_list = [ 'v1', self.ad['tenantid'], self.args['container'], self.just_filename ]
                filepath = '/%s' % quote('/'.join(quoted_list))
                f = open(filename)
                if self.args['debug']:
                    self.conn.set_debuglevel(1)

                self.conn.request('HEAD', filepath, headers=self.headers)
                resp = self.conn.getresponse()
                resp.read()

                if resp.status == 404:
                    self.conn.request('PUT', filepath, body=f, headers=self.headers)
                    resp = self.conn.getresponse()
                    resp.read()

                    if self.args['verbose']:
                        print resp.status, resp.reason, self.just_filename

                if resp.status is None:
                    UploadAction.open_conn(self)
                    UploadAction.re_auth(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status == 401:
                    print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                    UploadAction.re_auth(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status == 400:
                    print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                    UploadAction.open_conn(self)
                    up_retry = True
                    self.error += 1
                    continue

                if resp.status >= 300:
                    print 'ERROR\t:', resp.status, resp.reason, self.just_filename, '\n', f, '\n'

                else:
                    remotemd5sum = resp.getheader('etag')
                    md5 = hashlib.md5()
                    with f as fmd5:
                        for chunk in iter(lambda : fmd5.read(128 * md5.block_size), ''):
                            md5.update(chunk)
                        fmd5.close()
                    localmd5sum = md5.hexdigest()

                    if remotemd5sum != localmd5sum:
                        f = open(filename)

                        if self.args['debug']:
                            self.conn.set_debuglevel(1)
                        self.conn.request('PUT', filepath, body=f, headers=self.headers)
                        f.close()

                        resp = self.conn.getresponse()
                        resp.read()

                        if self.args['verbose']:
                            print 'MESSAGE\t: CheckSumm Mis-Match %(lmd5)s != %(rmd5)s\n\t ' \
                                  'File Upload : %(rs)s %(rr)s %(sjf)s' \
                                  % { 'lmd5' : localmd5sum, 'rmd5' : remotemd5sum, 'rs' : resp.status,
                                      'rr' : resp.reason, 'sjf' : self.just_filename }


                        if resp.status is None:
                            UploadAction.open_conn(self)
                            UploadAction.re_auth(self)
                            up_retry = True
                            self.error += 1
                            continue

                        if resp.status == 401:
                            print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                            UploadAction.re_auth(self)
                            up_retry = True
                            self.error += 1
                            continue

                        if resp.status == 400:
                            print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                            UploadAction.open_conn(self)
                            up_retry = True
                            self.error += 1
                            continue

                        if resp.status >= 300:
                            print 'ERROR\t:', resp.status, resp.reason, self.just_filename, '\n', f, '\n'

                    else:
                        if self.args['verbose']:
                            print 'MESSAGE\t: CheckSumm Match', localmd5sum
        except IOError, e:
            if e.errno == errno.ENOENT:
                print 'ERROR\t: path "%s" does not exist or is a broken symlink' % filename
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % filename
        except KeyboardInterrupt:
            pass
        except:
            print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
