# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import urllib

import turbolift as clds
from turbolift import info
from turbolift.clouderator import cloud_utils
from turbolift import utils
from turbolift.worker import ARGS
from turbolift.worker import LOG


class cloud_actions(object):

    def __init__(self, payload):
        self.payload = payload

    def resp_exception(self, resp, rty):
        """If we encounter an exception in our upload.

        we will look at how we can attempt to resolve the exception.

        :param resp:
        :param authurl:
        """

        try:
            if resp.status == 401:
                print('MESSAGE\t: Forced Re-authentication is happening.')
                utils.stupid_hack()
                self.payload['headers']['X-Auth-Token'] = utils.get_new_token()
                print resp.getheaders(), resp.status
                rty()
            elif resp.status == 404:
                LOG.info(
                    'Object not found status %s, reason %s',
                    resp.status, resp.reason
                )
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                utils.stupid_hack(wait=_di.get('retry_after', 10))
                raise clds.SystemProblem(
                    'The System encountered an API limitation and will'
                    ' continue in %s Seconds' % _di.get('retry_after', 5)
                )
                rty()
            elif resp.status == 502:
                raise clds.SystemProblem('Failure making Connection')
            elif resp.status >= 300:
                raise clds.SystemProblem('NOVA-API FAILURE -> REQUEST')
        except clds.SystemProblem as exp:
            LOG.error(
                'FAILURE STATUS %s FAILURE REASON %s', resp.status, resp.reason
            )
            rty()

    def _container_create(self, url, container):
        """Create a continer if it is not Found.

        :param url:
        :param container:
        """

        for retry in utils.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=5):
            conn = utils.open_connection(url=url)
            rpath = urllib.quote('%s/%s' % (url.path, container))
            path = urllib.quote(rpath)

            # Check to see if the Container is found.
            try:
                conn.request('HEAD', rpath, headers=self.payload['headers'])
                resp = utils.response_get(conn=conn)
            except Exception as exp:
                print('ERROR\t: Shits broke son, -> Exception:\t %s' % exp)
                retry()
            else:
                self.resp_exception(resp=resp, rty=retry)
                try:
                    # Check that the status was a good one
                    if resp.status == 404:
                        print('Creating Container ==> %s' % container)

                        conn.request('PUT',
                                     rpath,
                                     headers=self.payload['headers'])
                        resp = utils.response_get(conn=conn)
                        print('Container "%s" Created' % container)
                    else:
                        print('Container "%s" Found' % container)
                except Exception as exp:
                    print('ERROR\t: Shits broke son, -> Exception:\t %s' % exp)
                    retry()
                else:
                    self.resp_exception(resp=resp, rty=retry)
            finally:
                conn.close()

    def _putter(self, conn, fpath, rpath, fheaders, retry):
        """Place  object into the container.

        :param conn:
        :param fpath:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        if ARGS.get('verbose'):
            print('Uploading local file %s to remote %s' % (fpath, rpath))
        try:
            with open(fpath, 'rb') as f_open:
                conn.request('PUT', rpath, body=f_open, headers=fheaders)
            resp = utils.response_get(conn=conn)
            self.resp_exception(resp=resp, rty=retry)
        except clds.SystemProblem:
            retry()
        else:
            if ARGS.get('verbose'):
                print('INFO\t: %s %s %s' % (resp.status, resp.reason, fpath))

    def object_putter(self, url, container, source, u_file):
        """This is the Sync method which uploads files to the swift repository

        if they are not already found. If a file "name" is found locally and
        in the swift repository an MD5 comparison is done between the two
        files. If the MD5 is miss-matched the local file is uploaded to the
        repository. If custom meta data is specified, and the object exists the
        method will put the metadata onto the object.

        :param url:
        :param container:
        :param source:
        :param u_file:
        """

        for retry in utils.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=5):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Get the path ready for action
            sfile = utils.get_sfile(ufile=u_file, source=source)
            rpath = urllib.quote(
                '%s/%s/%s' % (url.path, container, sfile)
            )

            # Upload File to Object
            try:
                if ARGS.get('sync'):
                    conn.request('HEAD',
                                 rpath,
                                 headers=self.payload['headers'])
                    resp = utils.response_get(conn=conn)
                    self.resp_exception(resp=resp, rty=retry)
                    if resp.status == 404:
                        # if not found, perform Upload.
                        self._putter(conn=conn,
                                     fpath=u_file,
                                     rpath=rpath,
                                     fheaders=self.payload['headers'],
                                     retry=retry)

                    elif cloud_utils.md5_checker(resp=resp,
                                                 local_f=u_file) is True:
                        # If different, perform Upload.
                        self._putter(conn=conn,
                                     fpath=u_file,
                                     rpath=rpath,
                                     fheaders=self.payload['headers'],
                                     retry=retry)
                else:
                    # Perform Upload.
                    self._putter(conn=conn,
                                 fpath=u_file,
                                 rpath=rpath,
                                 fheaders=self.payload['headers'],
                                 retry=retry)
            except IOError as exp:
                print('ERROR\t: IO issues when accessing file %s. ERROR %s'
                      '%s will retry.' % (u_file, exp, info.__appname__))
                LOG.error(exp)
                retry()
            except KeyboardInterrupt:
                pass
            except Exception as exp:
                print('Failed operation, Error %s on %s. %s will retry'
                      % (exp, u_file, info.__appname__))
                LOG.error(exp)
                retry()
            else:
                # Put headers on the object if custom headers
                if ARGS.get('object_headers'):
                    conn.request('POST', remote_path, headers=f_headers)
                    resp = utils.response_get(conn=conn)
                    self.resp_exception(resp=resp, rty=retry)
            finally:
                conn.close()
