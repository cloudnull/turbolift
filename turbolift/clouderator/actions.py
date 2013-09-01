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
import turbolift.clouderator as crds
import turbolift.methods as mlds
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
        :param rty:
        """

        try:
            if resp.status == 401:
                print('MESSAGE\t: Forced Re-authentication is happening.')
                utils.stupid_hack()
                self.payload['headers']['X-Auth-Token'] = utils.get_new_token()
                rty()
            elif resp.status == 404:
                LOG.info(
                    'Object not found status %s, reason %s',
                    resp.status, resp.reason
                )
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                utils.stupid_hack(wait=_di.get('retry_after', 10))
                rty()
                raise clds.SystemProblem(
                    'The System encountered an API limitation and will'
                    ' continue in "%s" Seconds' % _di.get('retry_after', 5)
                )
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

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                conn.request(
                    'HEAD', rpath, headers=self.payload['headers']
                )
                resp, read = utils.response_get(conn=conn)

                self.resp_exception(resp=resp, rty=retry)
                try:
                    # Check that the status was a good one
                    if resp.status == 404:
                        print('Creating Container ==> %s' % container)
                        conn.request(
                            'PUT', rpath, headers=self.payload['headers']
                        )
                        resp, read = utils.response_get(conn=conn)
                        print('Container "%s" Created' % container)
                    else:
                        print('Container "%s" Found' % container)
                except Exception as exp:
                    print('ERROR\t: Shits broke son, -> Exception:\t %s' % exp)
                    retry()
                else:
                    self.resp_exception(resp=resp, rty=retry)

    def _deleter(self, conn, rpath, fheaders, retry):
        """Place  object into the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object Delete
        conn.request('DELETE', rpath, headers=fheaders)

        resp, read = utils.response_get(conn=conn)
        self.resp_exception(resp=resp, rty=retry)

        if ARGS.get('verbose'):
            print('INFO: %s %s %s' % (resp.status, resp.reason, resp.msg))

    def _putter(self, conn, fpath, rpath, fheaders, retry):
        """Place  object into the container.

        :param conn:
        :param fpath:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        LOG.debug('Uploading local file %s to remote %s', fpath, rpath)

        def _checker(conn, fpath, retry, fheaders):
            # Upload File to Object
            if ARGS.get('sync'):
                conn.request(
                    'HEAD', rpath, headers=fheaders
                )
                resp, read = utils.response_get(conn=conn)
                self.resp_exception(resp=resp, rty=retry)
                if resp.status == 404:
                    return True
                elif crds.md5_checker(resp=resp, local_f=fpath) is True:
                    return True
                else:
                    return False
            else:
                return True

        if _checker(conn, fpath, retry, fheaders) is True:
            with open(fpath, 'r') as f_open:
                conn.request(
                    'PUT', rpath, body=f_open, headers=fheaders
                )
            # While the file should be closed, we are making sure.
            f_open.close()

            resp, read = utils.response_get(conn=conn)
            self.resp_exception(resp=resp, rty=retry)

            if ARGS.get('verbose'):
                print('INFO: %s %s %s' % (resp.status, resp.reason, resp.msg))

    def _list_getter(self, conn, count, filepath, headers):
        """Get a list of all objects in a container.

        :param conn:
        :param count:
        :param filepath:
        :param headers:
        :return list:
        """
        file_l = []
        fpath = filepath
        for _ in xrange(count / 10000 + 1):
            for rty in utils.retryloop(attempts=ARGS.get('error_retry')):
                with mlds.operation(rty):
                    # Make a connection
                    conn.request(
                        'GET', fpath, headers=headers
                    )
                    resp, read = utils.response_get(conn=conn)
                    self.resp_exception(resp=resp, rty=rty)

                    for obj in utils.json_encode(read):
                        file_l.append(
                            {'name': obj.get('name'),
                             'hash': obj.get('hash'),
                             'bytes': obj.get('bytes')}
                        )

                    lobj = file_l[-1].get('name')
                    fpath = (
                        '%s&marker=%s' % (filepath, urllib.quote(lobj))
                    )
        final_list = utils.unique_list_dicts(dlist=file_l, key='name')
        msg = 'INFO: %s object(s) found' % len(final_list)
        if ARGS.get('verbose'):
            print(msg)

        LOG.info(msg)
        return final_list

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
        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry):
                # Get the path ready for action
                sfile = utils.get_sfile(ufile=u_file, source=source)
                rpath = urllib.quote(
                    '%s/%s/%s' % (url.path, container, sfile)
                )
                # Perform Upload.
                self._putter(conn=conn,
                             fpath=u_file,
                             rpath=rpath,
                             fheaders=self.payload['headers'],
                             retry=retry)

                # Put headers on the object if custom headers
                if ARGS.get('object_headers'):
                    conn.request('POST', remote_path, headers=f_headers)
                    resp, read = utils.response_get(conn=conn)
                    LOG.debug(read)
                    self.resp_exception(resp=resp, rty=retry)

    def object_deleter(self, url, container, u_file):
        """Delete all objects in a container.

        :param url:
        :param container:
        :param u_file:
        :return:
        """

        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry):
                rpath = urllib.quote(
                    '%s/%s/%s' % (url.path, container, u_file)
                )
                # Perform delete.
                self._deleter(conn=conn,
                              rpath=rpath,
                              fheaders=self.payload['headers'],
                              retry=retry)

    def object_lister(self, url, container):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :param container:
        """

        last_obj = None
        for retry in utils.retryloop(attempts=ARGS.get('error_retry')):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                # Determine how many files are in the container
                fpath = urllib.quote(
                    '%s/%s' % (url.path, container)
                )

                # Make a connection
                conn.request(
                    'HEAD', fpath, headers=self.payload['headers']
                )
                resp, read = utils.response_get(conn=conn)

                head_check = dict(resp.getheaders())
                object_count = head_check.get('x-container-object-count')

                if object_count:
                    object_count = int(object_count)
                    if not object_count > 0:
                        return None
                else:
                    return None

                self.resp_exception(resp=resp, rty=retry)
                if resp.status == 404:
                    conn.close()
                    LOG.debug('Not found. %s | %s' % (resp.status, resp.msg))
                    return False
                else:
                    count = int(resp.getheader('X-Container-Object-Count'))

                    # Set the number of loops that we are going to do
                    _fpath = '%s/?limit=10000&format=json' % fpath
                    headers = self.payload['headers']
                    headers.update({'Content-type': 'application/json'})
                    return self._list_getter(
                        conn=conn,
                        count=count,
                        filepath=_fpath,
                        headers=headers
                    )
