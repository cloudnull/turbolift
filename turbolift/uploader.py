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
import errno
import hashlib
import time
from urllib import quote

# Local Files to Import
import authentication


class UploadAction:

    def __init__(self, tur_arg, authdata, filename=None, gfn_count=None):
        self.ad = authdata
        self.args = tur_arg
        self.error = 0

        if self.args.compress:
            self.open_conn(self)
            self.just_filename = os.path.basename(filename)
            self.put_uploader(filename)
            self.conn.close()
        
        else:
            self.open_conn(self)

            while True:
                try:
                    item = filename.get()
                    if item is ('STOP' or None):
                        time.sleep(.01)
                        break
                    self.just_filename = item.split(os.path.realpath(self.args.source) + os.sep)[1]
                    if self.args.upload:
                        self.put_uploader(item)
                    elif self.args.tsync:
                        self.sync_uploader(item)
                    else:
                        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
                    time.sleep(.01)
                except:
                    break
        self.conn.close()


    def re_auth(self, authdata=None):
        au = authentication.NovaAuth(self.args)
        self.ad = au.osauth(self.args)
        return self


    def open_conn(self, authdata=None):
        endpoint = self.ad['endpoint'].split('/')[2]
        self.headers = {'X-Auth-Token': self.ad['token']}
        self.conn = httplib.HTTPSConnection(endpoint, 443)
        return self


    def put_uploader(self, filename):
        try:
            retry = True
            while retry:
                retry = False
                if self.error >= 5:
                    print 'ERROR\t: The Application attempted to retry too many times.'
                    print 'ERROR\t: Retry attempts were %s' % self.retry
                    break
                filepath = '/v1/' + self.ad['tenantid'] + '/' + quote(self.args.container + '/' + self.just_filename)
                f = open(filename)
                
                if self.args.debug:
                    self.conn.set_debuglevel(1)
                
                self.conn.request('PUT', filepath, body=f, headers=self.headers)
                time.sleep(.5)
                f.close()

                resp = self.conn.getresponse()
                resp.read()

                if self.args.progress:
                    print resp.status, resp.reason, self.just_filename
            
                if resp.status == 401:
                    print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                    UploadAction.re_auth(self, self.args)
                    retry = True
                    continue
                        
                if resp.status == 400:
                    print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                    self.open_conn(self)
                    retry = True
                    continue

                if resp.status >= 300:
                    print 'ERROR\t:', resp.status, resp.reason, self.just_filename, '\n', f, '\n'

        except IOError, e:
            if e.errno == errno.ENOENT:
                print 'ERROR\t: path "%s" does not exist or is a broken symlink' % filename
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % filename
        except KeyboardInterrupt, e:
            pass
        except:
            print 'ERROR\t: Shits broke son, here comes the stack trace :\n', sys.exc_info()[1]


    def sync_uploader(self, filename):
        try:
            retry = True
            while retry:
                retry = False
                if self.error >= 5:
                    print 'ERROR\t: The Application attempted to retry too many times.'
                    print 'ERROR\t: Retry attempts were %s' % self.retry
                    break
                
                filepath = '/v1/' + self.ad['tenantid'] + '/' + quote(self.args.container + '/' + self.just_filename)
                f = open(filename)
                
                if self.args.debug:
                    self.conn.set_debuglevel(1)
                
                self.conn.request('HEAD', filepath, headers=self.headers)
                resp = self.conn.getresponse()
                resp.read()

                if resp.status == 404:
                    self.conn.request('PUT', filepath, body=f, headers=self.headers)
                    time.sleep(.5)
                    resp = self.conn.getresponse()
                    resp.read()
                    
                    if self.args.progress:
                        print resp.status, resp.reason, self.just_filename
            
                    if resp.status == 401:
                        print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                        UploadAction.re_auth(self, self.args)
                        retry = True
                        continue
                    
                    if resp.status == 400:
                        print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                        self.open_conn(self)
                        retry = True
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
                        
                        if self.args.debug:
                            self.conn.set_debuglevel(1)
                        self.conn.request('PUT', filepath, body=f, headers=self.headers)
                        time.sleep(.5)
                        f.close()

                        resp = self.conn.getresponse()
                        resp.read()
                        
                        if self.args.progress:
                            print 'MESSAGE\t: CheckSumm Mis-Match', localmd5sum, '!=', remotemd5sum, '\n\t ', 'File Upload :', resp.status, resp.reason, self.just_filename
                        
                        if resp.status == 401:
                            print 'MESSAGE\t: Token Seems to have expired, Forced Re-authentication is happening.'
                            UploadAction.re_auth(self, self.args)
                            retry = True
                            continue
                        
                        if resp.status == 400:
                            print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
                            self.open_conn(self)
                            retry = True
                            continue
                    
                        if resp.status >= 300:
                            print 'ERROR\t:', resp.status, resp.reason, self.just_filename, '\n', f, '\n'
                        
                    else:
                        if self.args.progress:
                            print 'MESSAGE\t: CheckSumm Match', localmd5sum
        except IOError, e:
            if e.errno == errno.ENOENT:
                print 'ERROR\t: path "%s" does not exist or is a broken symlink' % filename
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % filename
        except KeyboardInterrupt, e:
            pass
        except:
            print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
