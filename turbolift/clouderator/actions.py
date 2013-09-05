# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import tempfile
import urllib

import turbolift as clds
import turbolift.clouderator as crds
import turbolift.methods as mlds
from turbolift import utils
from turbolift.worker import ARGS


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
                    lvl='error',
                    log=True
                )
                utils.stupid_hack()
                self.payload['headers']['X-Auth-Token'] = utils.get_new_token()
                rty()
            elif resp.status == 404:
                utils.reporter(
                    msg=('Not found STATUS: %s, REASON: %s, MESSAGE: %s'
                         % (resp.status, resp.reason, resp.msg)),
                    prt=False,
                    lvl='debug'
                )
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                utils.stupid_hack(wait=_di.get('retry_after', 10))
                raise clds.SystemProblem(
                    'The System encountered an API limitation and will'
                    ' continue in "%s" Seconds' % _di.get('retry_after')
                )
            elif resp.status == 502:
                raise clds.SystemProblem('Failure making Connection')
            elif resp.status == 503:
                utils.stupid_hack(wait=10)
                raise clds.SystemProblem('503')
            elif resp.status >= 300:
                raise clds.SystemProblem('NOVA-API FAILURE -> REQUEST')
        except clds.SystemProblem as exp:
            utils.reporter(
                msg=('FAIL-MESSAGE %s FAILURE STATUS %s FAILURE REASON %s '
                     'TYPE %s MESSAGE %s' % (exp, resp.status, resp.reason,
                                             resp._method, resp.msg)),
                prt=True,
                lvl='error',
                log=True
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
            resp = self._header_getter(conn=conn,
                                       rpath=rpath,
                                       fheaders=fheaders,
                                       retry=retry)
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

            rpath = self._quoter(url=url.path,
                                 cont=container)

            # Open connection and perform operation
            with mlds.operation(retry, conn):

                resp = self._header_getter(conn=conn,
                                           rpath=rpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)

                # Check that the status was a good one
                if resp.status == 404:
                    utils.reporter(msg='Creating Container ==> %s' % container)

                    conn.request('PUT', rpath, headers=self.payload['headers'])
                    resp, read = utils.response_get(conn=conn, retry=retry)
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
            utils.reporter(
                msg='Downloading remote %s to local file %s' % (rpath, lfile),
                prt=False,
                lvl='debug',
            )

            # Perform Object GET
            conn.request('GET', rpath, headers=fheaders)
            # Open our source file and write it
            with open(local_f, 'ab') as f_name:
                resp = utils.response_get(conn=conn,
                                          retry=retry,
                                          resp_only=True)
                self.resp_exception(resp=resp, rty=retry)
                if resp is None:
                    utils.reporter(
                        msg='API Response Was NONE. resp was: %s' % resp.msg,
                        prt=True,
                        lvl='error',
                        log=True
                    )
                    retry()
                else:
                    while True:
                        chunk = resp.read(2048)
                        if not chunk:
                            break
                        else:
                            f_name.write(chunk)

            utils.reporter(
                msg=('OBJECT %s MESSAGE %s %s %s'
                     % (rpath, resp.status, resp.reason, resp.msg)),
                prt=False,
                lvl='debug'
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

        resp, read = utils.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg=('OBJECT %s MESSAGE %s %s %s'
                 % (rpath, resp.status, resp.reason, resp.msg)),
            prt=False,
            lvl='debug'
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
                msg='OBJECT ORIGIN %s RPATH %s' % (fpath, rpath),
                prt=False,
                lvl='debug'
            )
            with open(fpath, 'rb') as f_open:
                conn.request('PUT', rpath, body=f_open, headers=fheaders)
            resp, read = utils.response_get(conn=conn, retry=retry)
            self.resp_exception(resp=resp, rty=retry)

            utils.reporter(
                msg=('MESSAGE %s %s %s'
                     % (resp.status, resp.reason, resp.msg)),
                prt=False,
                lvl='debug'
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
            for retry in utils.retryloop(attempts=ARGS.get('error_retry')):
                with mlds.operation(retry):
                    # Make a connection
                    conn.request('GET', fpath, headers=fheaders)
                    resp, read = utils.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)
                    for obj in utils.json_encode(read):
                        if ARGS.get('time_offset') is not None:
                            # Get the last_modified data from the Object
                            lmobj = obj.get('last_modified')
                            if crds.time_delta(lmobj=lmobj) is True:
                                file_l.append(obj)
                        else:
                            file_l.append(obj)

                    if file_l:
                        lobj = file_l[-1].get('name')
                        fpath = '%s&marker=%s' % (utils.ustr(filepath),
                                                  utils.ustr(lobj))
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
        resp, read = utils.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg='INFO: %s %s %s' % (resp.status, resp.reason, resp.msg),
            prt=False
        )

        return resp

    def _header_poster(self, conn, rpath, fheaders, retry):
        """POST Headers on a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object POST request for header update.
        conn.request('POST', rpath, headers=fheaders)
        resp, read = utils.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        utils.reporter(
            msg=('STATUS: %s MESSAGE: %s REASON: %s'
                 % (resp.status, resp.msg, resp.reason)),
            prt=False,
            lvl='debug'
        )

        return dict(resp.getheaders())

    def _quoter(self, url, cont=None, ufile=None):
        """Return a Quoted URL.

        :param url:
        :param cont:
        :param ufile:
        :return:
        """

        url = utils.ustr(obj=url)
        if cont is not None:
            cont = utils.ustr(obj=cont)
        if ufile is not None:
            ufile = utils.ustr(obj=ufile)

        if ufile is not None and cont is not None:
            return urllib.quote(
                '%s/%s/%s' % (url, cont, ufile)
            )
        elif cont is not None:
            return urllib.quote(
                '%s/%s' % (url, cont)
            )
        else:
            return urllib.quote(
                '%s' % url
            )

    def container_cdn_command(self, url, container, sfile=None):
        """Command your CDN enabled Container.

        :param url:
        :param container:
        """

        for retry in utils.retryloop(attempts=5, delay=2):
            # Open Connection
            conn = utils.open_connection(url=url)
            with mlds.operation(retry, conn):
                cheaders = self.payload['headers']
                if sfile is not None:
                    rpath = self._quoter(url=url.path,
                                         cont=container,
                                         ufile=sfile)
                    # perform CDN Object DELETE
                    conn.request('DELETE', rpath, headers=cheaders)
                    resp, read = utils.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)
                else:
                    rpath = self._quoter(url=url.path,
                                         cont=container)
                    endis = ARGS.get('enabled', ARGS.get('disable', False))
                    cheaders.update({'X-CDN-Enabled': endis,
                                     'X-TTL': ARGS.get('cdn_ttl'),
                                     'X-Log-Retention': ARGS.get('cdn_logs')})
                    # perform CDN Enable POST
                    conn.request('PUT', rpath, headers=cheaders)
                    resp, read = utils.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)

                utils.reporter(
                    msg=('OBJECT %s MESSAGE %s %s %s'
                         % (rpath, resp.status, resp.reason, resp.msg)),
                    prt=False,
                    lvl='debug'
                )

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
                rpath = self._quoter(url=url.path,
                                     cont=container)
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

        for retry in utils.retryloop(attempts=ARGS.get('error_retry')):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                # Determine how many files are in the container
                fpath = self._quoter(url=url.path)

                # Make a connection
                resp = self._header_getter(conn=conn,
                                           rpath=fpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)

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
                rpath = self._quoter(url=url.path,
                                     cont=container,
                                     ufile=sfile)
                # Perform Upload.
                self._putter(conn=conn,
                             fpath=u_file,
                             rpath=rpath,
                             fheaders=self.payload['headers'],
                             retry=retry)

                # Put headers on the object if custom headers
                if ARGS.get('object_headers') is not None:
                    obh = self.payload['headers']
                    obh.update(ARGS.get('object_headers'))

                    self._header_poster(
                        conn=conn, rpath=rpath, fheaders=obh, retry=retry
                    )

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
                rpath = self._quoter(url=url.path,
                                     cont=container,
                                     ufile=u_file)

                # Make a connection
                resp = self._header_getter(conn=conn,
                                           rpath=rpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)
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

            # Perform operation
            with mlds.operation(retry, conn):
                rpath = self._quoter(url=url.path,
                                     cont=container,
                                     ufile=u_file)
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

        for retry in utils.retryloop(attempts=ARGS.get('error_retry')):
            # Open Connection
            conn = utils.open_connection(url=url)

            # Open connection and perform operation
            with mlds.operation(retry, conn):
                # Determine how many files are in the container
                fpath = self._quoter(url=url.path,
                                     cont=container)
                # Make a connection
                resp = self._header_getter(conn=conn,
                                           rpath=fpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)

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

        def _cleanup():
            """Ensure that our temp file is removed."""
            try:
                os.remove(tfile)
            except OSError:
                pass

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
        for retry in utils.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=5):
            # Open connection and perform operation
            fmt, date, date_delta, now = utils.time_stamp()
            spath = self._quoter(url=surl.path,
                                 cont=scontainer,
                                 ufile=obj['name'])
            tpath = self._quoter(url=turl.path,
                                 cont=tcontainer,
                                 ufile=obj['name'])
            try:
                # Open Connection
                conn = utils.open_connection(url=surl)
                with mlds.operation(retry,
                                    conn=conn,
                                    obj=obj,
                                    cleanup=_cleanup):
                    # make a temp file.
                    tfile = tempfile.mktemp()

                    # Make a connection
                    resp = self._header_getter(conn=conn,
                                               rpath=spath,
                                               fheaders=fheaders,
                                               retry=retry)
                    sheaders = dict(resp.getheaders())

                    # TODO(kevin) add the ability to short upload if timestamp
                    # TODO(kevin) ... is newer on the target.
                    #x_timestamp = resp.getheader('x-timestamp')

                    # GET remote Object
                    _dl = self._downloader(conn=conn,
                                           rpath=spath,
                                           fheaders=fheaders,
                                           lfile=tfile,
                                           source=None,
                                           retry=retry,
                                           skip=True)
                    if _dl is False:
                        retry()

                conn = utils.open_connection(url=turl)
                with mlds.operation(retry,
                                    conn=conn,
                                    obj=obj,
                                    cleanup=_cleanup):
                    resp = self._header_getter(conn=conn,
                                               rpath=tpath,
                                               fheaders=fheaders,
                                               retry=retry)

                    # If object comparison is True GET then PUT object
                    if _compare(resp=resp, obj=obj) is True:
                        self.resp_exception(resp=resp, rty=retry)
                        # PUT remote object
                        self._putter(conn=conn,
                                     fpath=tfile,
                                     rpath=tpath,
                                     fheaders=fheaders,
                                     retry=retry,
                                     skip=True)
                        # let the system rest for 3 seconds.
                        utils.stupid_hack(wait=3)

                    # With the retrieved headers POST new headers on the obj.
                    if ARGS.get('clone_headers') is True:
                        resp = self._header_getter(conn=conn,
                                                   rpath=tpath,
                                                   fheaders=fheaders,
                                                   retry=retry)
                        theaders = dict(resp.getheaders())
                        for key in sheaders.keys():
                            if key not in theaders:
                                fheaders.update({key: sheaders[key]})
                        # Force the SOURCE content Type on the Target.
                        fheaders.update(
                            {'content-type': sheaders.get('content-type')}
                        )
                        self._header_poster(
                            conn=conn,
                            rpath=tpath,
                            fheaders=fheaders,
                            retry=retry
                        )
            finally:
                _cleanup()
