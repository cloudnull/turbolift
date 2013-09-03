# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import datetime
import os
import tempfile
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
                utils.reporter(
                    msg='MESSAGE: Forced Re-authentication is happening.',
                    lvl='error'
                )
                utils.stupid_hack()
                self.payload['headers']['X-Auth-Token'] = utils.get_new_token()
                rty()
            elif resp.status == 404:
                utils.reporter(
                    msg=('Not found STATUS: %s, REASON: %s, MESSAGE: %s'
                         % (resp.status, resp.reason, resp.msg)),
                    prt=False
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

    def _checker(self, conn, rpath, lpath, fheaders, retry, skip):
        """Check to see if a local file and a target file are different.

        :param conn:
        :param rpath:
        :param lpath:
        :param retry:
        :param fheaders:
        :return True|False:
        """
        # Upload File to Object
        if skip is True:
            return True
        elif ARGS.get('sync'):
            conn.request('HEAD', rpath, headers=fheaders)
            resp, read = utils.response_get(conn=conn)
            self.resp_exception(resp=resp, rty=retry)
            if resp.status == 404:
                return True
            elif crds.md5_checker(resp=resp, local_f=lpath) is True:
                return True
            else:
                return False
        else:
            return True

    def _container_create(self, url, container):
        """Create a continer if it is not Found.

        :param url:
        :param container:
        """

        rty_count = ARGS.get('error_retry')
        for retry in utils.retryloop(attempts=rty_count, delay=5):
            conn = utils.open_connection(url=url)
            rpath = urllib.quote('%s/%s' % (url.path, container))
            path = urllib.quote(rpath)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                conn.request('HEAD', rpath, headers=self.payload['headers'])
                resp, read = utils.response_get(conn=conn)
                self.resp_exception(resp=resp, rty=retry)

                # Check that the status was a good one
                if resp.status == 404:
                    utils.reporter(msg='Creating Container ==> %s' % container)

                    conn.request('PUT', rpath, headers=self.payload['headers'])
                    resp, read = utils.response_get(conn=conn)
                    self.resp_exception(resp=resp, rty=retry)

                    utils.reporter(msg='Container "%s" Created' % container)
                    return True
                else:
                    utils.reporter(msg='Container "%s" Found' % container)
                    return False

    def _downloader(self, conn, rpath, fheaders, lfile, source, retry,
                    skip=False):
        """Download a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param lfile:
        :param retry:
        :param skip:
        """

        if source is None:
            local_f = lfile
        else:
            local_f = os.path.join(source, lfile)

        if self._checker(conn, rpath, local_f, fheaders, retry, skip) is True:
            LOG.debug('Downloading remote %s to local file %s', lfile, rpath)

            # perform Object Download
            conn.request('GET', rpath, headers=fheaders)
            resp, read = utils.response_get(conn=conn)
            self.resp_exception(resp=resp, rty=retry)

            # Open our source file and write it
            with open(local_f, 'wb') as f_name:
                f_name.write(read)

            utils.reporter(
                msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
                prt=False
            )

    def _deleter(self, conn, rpath, fheaders, retry):
        """Delete a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object Delete
        conn.request('DELETE', rpath, headers=fheaders)

        resp, read = utils.response_get(conn=conn)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
            prt=False
        )

    def _putter(self, conn, fpath, rpath, fheaders, retry, skip=False):
        """Place  object into the container.

        :param conn:
        :param fpath:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        if self._checker(conn, rpath, fpath, fheaders, retry, skip) is True:
            utils.reporter(
                msg=('SOURCE: %s => REMOTE: %s' % (fpath, rpath)),
                lvl='debug',
                prt=False
            )
            with open(fpath, 'r') as f_open:
                conn.request('PUT', rpath, body=f_open, headers=fheaders)

            resp, read = utils.response_get(conn=conn)
            self.resp_exception(resp=resp, rty=retry)

            utils.reporter(
                msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
                prt=False
            )

    def _list_getter(self, conn, count, filepath, fheaders):
        """Get a list of all objects in a container.

        :param conn:
        :param count:
        :param filepath:
        :param fheaders:
        :return list:
        """

        file_l = []
        fpath = filepath
        for _ in xrange(count / 10000 + 1):
            for rty in utils.retryloop(attempts=ARGS.get('error_retry')):
                with mlds.operation(rty):
                    # Make a connection
                    conn.request('GET', fpath, headers=fheaders)
                    resp, read = utils.response_get(conn=conn)
                    self.resp_exception(resp=resp, rty=rty)

                    for obj in utils.json_encode(read):
                        if ARGS.get('time_offset') is not None:
                            # Get the last_modified data from the Object
                            lmobj=obj.get('last_modified')
                            if crds.time_delta(lmobj=lmobj) is True:
                                file_l.append(obj)
                        else:
                            file_l.append(obj)

                    if file_l:
                        lobj = file_l[-1].get('name')
                        fpath = (
                            '%s&marker=%s' % (filepath, urllib.quote(lobj))
                        )
        final_list = utils.unique_list_dicts(dlist=file_l, key='name')
        utils.reporter(
            msg='INFO: %s object(s) found' % len(final_list),
            log=True
        )
        return final_list

    def _header_getter(self, conn, rpath, fheaders, retry):
        """perfrom HEAD request on a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object HEAD request
        conn.request('HEAD', rpath, headers=fheaders)

        resp, read = utils.response_get(conn=conn)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
            prt=False
        )

        return dict(resp.getheaders())

    def _header_poster(self, conn, rpath, fheaders, retry):
        """POST Headers on a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object POST request for header update.
        conn.request('POST', rpath, headers=fheaders)

        resp, read = utils.response_get(conn=conn)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
            prt=False
        )

        return dict(resp.getheaders())

    def container_deleter(self, url, container):
        """Delete all objects in a container.

        :param url:
        :param container:
        """

        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                rpath = urllib.quote(
                    '%s/%s' % (url.path, container)
                )
                # Perform delete.
                self._deleter(conn=conn,
                              rpath=rpath,
                              fheaders=self.payload['headers'],
                              retry=retry)

    def container_lister(self, url):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :return None | list:
        """

        last_obj = None
        for retry in utils.retryloop(attempts=ARGS.get('error_retry')):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                # Determine how many files are in the container
                fpath = urllib.quote('%s' % url.path)

                # Make a connection
                conn.request('HEAD', fpath, headers=self.payload['headers'])
                resp, read = utils.response_get(conn=conn)
                self.resp_exception(resp=resp, rty=retry)

                head_check = dict(resp.getheaders())
                container_count = head_check.get('x-account-container-count')
                if container_count:
                    container_count = int(container_count)
                    if not container_count > 0:
                        return None
                else:
                    return None

                # Set the number of loops that we are going to do
                _fpath = '%s/?limit=10000&format=json' % fpath
                return self._list_getter(
                    conn=conn,
                    count=container_count,
                    filepath=_fpath,
                    fheaders=self.payload['headers']
                )

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
            with mlds.operation(retry, conn):
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
        """Deletes an objects in a container.

        :param url:
        :param container:
        :param u_file:
        """

        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                rpath = urllib.quote(
                    '%s/%s/%s' % (url.path, container, u_file)
                )

                # Make a connection
                conn.request('HEAD', rpath, headers=self.payload['headers'])
                resp, read = utils.response_get(conn=conn)
                self.resp_exception(resp=resp, rty=retry)

                if not resp.status == 404:
                    # Perform delete.
                    self._deleter(conn=conn,
                                  rpath=rpath,
                                  fheaders=self.payload['headers'],
                                  retry=retry)

    def object_downloader(self, url, container, source, u_file):
        """Download an Object from a Container.

        :param url:
        :param container:
        :param u_file:
        """

        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                rpath = urllib.quote(
                    '%s/%s/%s' % (url.path, container, u_file)
                )
                # Perform Download.
                self._downloader(conn=conn,
                                 rpath=rpath,
                                 fheaders=self.payload['headers'],
                                 lfile=u_file,
                                 source=source,
                                 retry=retry)

    def object_lister(self, url, container):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :param container:
        :return None | list:
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
                conn.request('HEAD', fpath, headers=self.payload['headers'])
                resp, read = utils.response_get(conn=conn)
                self.resp_exception(resp=resp, rty=retry)

                if not resp.status == 404:
                    head_check = dict(resp.getheaders())
                    object_count = head_check.get('x-container-object-count')
                    if object_count:
                        object_count = int(object_count)
                        if not object_count > 0:
                            return None
                    else:
                        return None
                else:
                    return False

                if resp.status == 404:
                    utils.reporter(
                        msg='Not found. %s | %s' % (resp.status, resp.msg)
                    )
                    return None
                else:
                    # Set the number of loops that we are going to do
                    _fpath = '%s/?limit=10000&format=json' % fpath
                    return self._list_getter(
                        conn=conn,
                        count=object_count,
                        filepath=_fpath,
                        fheaders=self.payload['headers']
                    )

    def object_syncer(self, surl, turl, scontainer, tcontainer, obj):
        """Download an Object from one Container and the upload it to a target.

        :param surl:
        :param turl:
        :param scontainer:
        :param tcontainer:
        :param obj:
        """

        def _time_difference(resp, obj):
            if ARGS.get('save_newer') is True:
                # Get the source object last modified time.
                compare_time = resp.getheader('last_modified')
                if crds.time_delta(compare_time=compare_time,
                                   lmobj=obj['last_modified']) is True:
                    return False
                else:
                    return True
            else:
                return True

        def _compare(resp, obj):
            if resp.status == 404:
                utils.reporter(
                    msg='Target Object %s not found' % obj['name'],
                    prt=False
                )
                return True
            elif resp.getheader('etag') != obj['hash']:
                utils.reporter(
                    msg='Checksum Mismatch on Target Object %s' % obj['name'],
                    prt=False
                )
                return _time_difference(resp, obj)
            else:
                return _time_difference(resp, obj)

        fheaders = self.payload['headers']
        for retry in utils.retryloop(attempts=5, delay=2):
            # Open connection and perform operation
            fmt, date, date_delta, now = utils.time_stamp()

            with mlds.operation(retry):
                spath = urllib.quote(
                    '%s/%s/%s' % (surl.path, scontainer, obj['name'])
                )
                tpath = urllib.quote(
                    '%s/%s/%s' % (turl.path, tcontainer, obj['name'])
                )

                # Open Connection
                tconn = utils.open_connection(url=turl)
                conn = utils.open_connection(url=surl)

                try:
                    conn.request('HEAD', spath, headers=fheaders)
                    resp, tread = utils.response_get(conn=conn)
                    x_timestamp = resp.getheader('x-timestamp')

                    tconn.request('HEAD', tpath, headers=fheaders)
                    tresp, tread = utils.response_get(conn=tconn)

                    # If object comparison is True GET then PUT object
                    if _compare(resp=tresp, obj=obj) is True:
                        self.resp_exception(resp=tresp, rty=retry)
                        try:
                            tfile = tempfile.mktemp()
                            # GET remote Object
                            self._downloader(conn=conn,
                                             rpath=spath,
                                             fheaders=fheaders,
                                             lfile=tfile,
                                             source=None,
                                             retry=retry,
                                             skip=True)

                            # let the system rest for a max of 2 seconds.
                            utils.stupid_hack(max=2)
                            fheaders.update(
                                {'X-timestamp': x_timestamp}
                            )
                            # PUT remote object
                            self._putter(conn=tconn,
                                         fpath=tfile,
                                         rpath=tpath,
                                         fheaders=fheaders,
                                         retry=retry,
                                         skip=True)
                        finally:
                            try:
                                os.remove(tfile)
                            except OSError:
                                pass

                    # With the retrieved headers POST new headers on the obj.
                    if ARGS.get('clone_headers') is True:
                        sheaders = self._header_getter(conn=conn,
                                                       rpath=spath,
                                                       fheaders=fheaders,
                                                       retry=retry)

                        theaders = self._header_getter(conn=tconn,
                                                       rpath=spath,
                                                       fheaders=fheaders,
                                                       retry=retry)
                        for key in sheaders.keys():
                            if key not in theaders:
                                fheaders.update({key: sheaders[key]})
                        fheaders.update(
                            {'content-type': sheaders.get('content-type')}
                        )
                        self._header_poster(conn=tconn,
                                            rpath=tpath,
                                            fheaders=fheaders,
                                            retry=retry)
                finally:
                    # Manually close the open connections.
                    conn.close()
                    tconn.close()
