# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import turbolift as turbo
import turbolift.clouderator as cloud
import turbolift.methods as meth
import turbolift.utils.auth_utils as auth
import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.report_utils as report

from turbolift import ARGS


class CloudActions(object):
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
                report.reporter(
                    msg='MESSAGE: Forced Re-authentication is happening.',
                    lvl='error',
                    log=True
                )
                basic.stupid_hack()
                self.payload['headers']['X-Auth-Token'] = auth.get_new_token()
                rty()
            elif resp.status == 404:
                report.reporter(
                    msg=('Not found STATUS: %s, REASON: %s, MESSAGE: %s'
                         % (resp.status, resp.reason, resp.msg)),
                    prt=False,
                    lvl='debug'
                )
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                basic.stupid_hack(wait=_di.get('retry_after', 10))
                raise turbo.SystemProblem(
                    'The System encountered an API limitation and will'
                    ' continue in "%s" Seconds' % _di.get('retry_after')
                )
            elif resp.status == 502:
                raise turbo.SystemProblem('Failure making Connection')
            elif resp.status == 503:
                basic.stupid_hack(wait=10)
                raise turbo.SystemProblem('SWIFT-API FAILURE')
            elif resp.status == 504:
                basic.stupid_hack(wait=10)
                raise turbo.SystemProblem('Gateway Time-out')
            elif resp.status >= 300:
                raise turbo.SystemProblem('SWIFT-API FAILURE -> REQUEST')
        except turbo.SystemProblem as exp:
            report.reporter(
                msg=('FAIL-MESSAGE %s FAILURE STATUS %s FAILURE REASON %s '
                     'TYPE %s MESSAGE %s' % (exp, resp.status, resp.reason,
                                             resp._method, resp.msg)),
                prt=True,
                lvl='warn',
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

        if skip is True:
            return True
        elif ARGS.get('sync'):
            resp = self._header_getter(conn=conn,
                                       rpath=rpath,
                                       fheaders=fheaders,
                                       retry=retry)
            if resp.status == 404:
                return True
            elif cloud.md5_checker(resp=resp, local_f=lpath) is True:
                return True
            else:
                return False
        else:
            return True

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
            local_f = basic.jpath(root=source, inode=lfile)

        if self._checker(conn, rpath, local_f, fheaders, retry, skip) is True:
            report.reporter(
                msg='Downloading remote %s to local file %s' % (rpath, lfile),
                prt=False,
                lvl='debug',
            )

            # Perform Object GET
            conn.request('GET', rpath, headers=fheaders)
            local_f = basic.collision_rename(file_name=local_f)

            # Open our source file and write it
            with open(local_f, 'ab') as f_name:
                resp = http.response_get(conn=conn,
                                         retry=retry,
                                         resp_only=True)
                self.resp_exception(resp=resp, rty=retry)
                if resp is None:
                    report.reporter(
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

            report.reporter(
                msg=('OBJECT %s MESSAGE %s %s %s'
                     % (rpath, resp.status, resp.reason, resp.msg)),
                prt=False,
                lvl='debug'
            )

        if ARGS.get('restore_perms') is not None:
            # Make a connection
            resp = self._header_getter(conn=conn,
                                       rpath=rpath,
                                       fheaders=fheaders,
                                       retry=retry)
            all_headers = dict(resp.getheaders())
            if all(['x-object-meta-group' in all_headers,
                    'x-object-meta-owner' in all_headers,
                    'x-object-meta-perms' in all_headers]):
                basic.restor_perms(local_file=local_f, headers=all_headers)
            else:
                report.reporter(
                    msg=('No Permissions were restored, because none were'
                         ' saved on the object "%s"' % rpath),
                    lvl='warn',
                    log=True
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

        resp, read = http.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        report.reporter(
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
            report.reporter(
                msg='OBJECT ORIGIN %s RPATH %s' % (fpath, rpath),
                prt=False,
                lvl='debug'
            )

            if basic.file_exists(fpath) is False:
                return None
            else:
                with open(fpath, 'rb') as f_open:
                    conn.request('PUT', rpath, body=f_open, headers=fheaders)
                resp, read = http.response_get(conn=conn, retry=retry)
                self.resp_exception(resp=resp, rty=retry)

                report.reporter(
                    msg=('MESSAGE %s %s %s'
                         % (resp.status, resp.reason, resp.msg)),
                    prt=False,
                    lvl='debug'
                )

    def _list_getter(self, conn, count, filepath, fheaders, last_obj=None):
        """Get a list of all objects in a container.

        :param conn:
        :param count:
        :param filepath:
        :param fheaders:
        :return list:
        """

        def _marker_type(base, last):
            """Set and return the marker.

            :param base:
            :param last:
            :return str:
            """

            if last is None:
                return base
            else:
                return _last_marker(f_path=base, l_obj=last)

        def _last_marker(f_path, l_obj):
            """Set Marker.

            :param f_path:
            :param l_obj:
            :return str:
            """

            return '%s&marker=%s' % (f_path, http.quoter(url=l_obj))

        def _obj_index(b_path, m_path, l_obj, f_list):
            conn.request('GET', m_path, headers=fheaders)
            resp, read = http.response_get(conn=conn, retry=retry)
            self.resp_exception(resp=resp, rty=retry)
            return_list = basic.json_encode(read)

            for obj in return_list:
                time_offset = ARGS.get('time_offset')
                if time_offset is not None:
                    # Get the last_modified data from the Object.
                    if cloud.time_delta(lmobj=time_offset) is True:
                        f_list.append(obj)
                else:
                    f_list.append(obj)

            last_obj_in_list = f_list[-1].get('name')
            if l_obj is last_obj_in_list:
                return f_list
            else:
                marker = _marker_type(base=b_path, last=last_obj_in_list)
                _obj_index(
                    b_path, marker, last_obj_in_list, f_list
                )

        # Quote the file path.
        base_path = marked_path = (
            '%s/?limit=10000&format=json' % basic.ustr(filepath)
        )
        if last_obj is not None:
            marked_path = _last_marker(
                f_path=base_path,
                l_obj=http.quoter(url=last_obj)
            )

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     obj='Object List Creation'):
            with meth.operation(retry):
                file_list = []
                _obj_index(
                    base_path, marked_path, last_obj, file_list
                )
                final_list = basic.unique_list_dicts(
                    dlist=file_list, key='name'
                )
                list_count = len(final_list)
                report.reporter(
                    msg='INFO: %d object(s) found' % len(final_list),
                    log=True
                )
                return final_list, list_count, last_obj

    def _header_getter(self, conn, rpath, fheaders, retry):
        """perfrom HEAD request on a specified object in the container.

        :param conn:
        :param rpath:
        :param fheaders:
        :param retry:
        """

        # perform Object HEAD request
        conn.request('HEAD', rpath, headers=fheaders)
        resp, read = http.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        report.reporter(
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
        resp, read = http.response_get(conn=conn, retry=retry)
        self.resp_exception(resp=resp, rty=retry)

        report.reporter(
            msg=('STATUS: %s MESSAGE: %s REASON: %s'
                 % (resp.status, resp.msg, resp.reason)),
            prt=False,
            lvl='debug'
        )

        return dict(resp.getheaders())

    def detail_show(self, url):
        """Return Details on an object or container."""

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count,
                                     delay=5,
                                     obj=ARGS.get('container')):
            conn = http.open_connection(url=url)
            if ARGS.get('object') is not None:
                rpath = http.quoter(url=url.path,
                                    cont=ARGS.get('container'),
                                    ufile=ARGS.get('object'))
            else:
                rpath = http.quoter(url=url.path,
                                    cont=ARGS.get('container'))

            resp = self._header_getter(conn=conn,
                                       rpath=rpath,
                                       fheaders=self.payload['headers'],
                                       retry=retry)
            if resp.status == 404:
                return 'Nothing found.'
            else:
                return resp.getheaders()

    def container_create(self, url, container):
        """Create a container if it is not Found.

        :param url:
        :param container:
        """

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count,
                                     delay=5,
                                     obj=container):
            conn = http.open_connection(url=url)

            rpath = http.quoter(url=url.path,
                                cont=container)

            # Open connection and perform operation
            with meth.operation(retry, conn):

                resp = self._header_getter(conn=conn,
                                           rpath=rpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)

                # Check that the status was a good one
                if resp.status == 404:
                    report.reporter(
                        msg='Creating Container ==> %s' % container
                    )

                    conn.request('PUT', rpath, headers=self.payload['headers'])
                    resp, read = http.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)

                    report.reporter(msg='Container "%s" Created' % container)
                    return True
                else:
                    report.reporter(msg='Container "%s" Found' % container)
                    return False

    def container_cdn_command(self, url, container, sfile=None):
        """Command your CDN enabled Container.

        :param url:
        :param container:
        """
        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count, delay=2, obj=sfile):
            # Open Connection
            conn = http.open_connection(url=url)
            with meth.operation(retry, conn):
                cheaders = self.payload['headers']
                if sfile is not None:
                    rpath = http.quoter(url=url.path,
                                        cont=container,
                                        ufile=sfile)
                    # perform CDN Object DELETE
                    conn.request('DELETE', rpath, headers=cheaders)
                    resp, read = http.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)
                else:
                    rpath = http.quoter(url=url.path,
                                        cont=container)
                    http.cdn_toggle(headers=cheaders)
                    # perform CDN Enable POST
                    conn.request('PUT', rpath, headers=cheaders)
                    resp, read = http.response_get(conn=conn, retry=retry)
                    self.resp_exception(resp=resp, rty=retry)

                report.reporter(
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

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=2,
                                     obj=container):
            # Open Connection
            conn = http.open_connection(url=url)

            # Open connection and perform operation
            with meth.operation(retry, conn):
                rpath = http.quoter(url=url.path,
                                    cont=container)
                # Perform delete.
                self._deleter(conn=conn,
                              rpath=rpath,
                              fheaders=self.payload['headers'],
                              retry=retry)

    def container_lister(self, url, last_obj=None):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :return None | list:
        """

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     obj='Container List'):
            # Open Connection
            conn = http.open_connection(url=url)

            # Open connection and perform operation
            with meth.operation(retry, conn):
                # Determine how many files are in the container
                fpath = http.quoter(url=url.path)

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
                return self._list_getter(conn=conn,
                                         count=container_count,
                                         filepath=fpath,
                                         fheaders=self.payload['headers'],
                                         last_obj=last_obj)

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

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=2,
                                     obj=u_file):
            # Open Connection
            conn = http.open_connection(url=url)

            # Open connection and perform operation
            with meth.operation(retry, conn, obj=u_file):
                # Get the path ready for action
                sfile = basic.get_sfile(ufile=u_file, source=source)
                rpath = http.quoter(url=url.path,
                                    cont=container,
                                    ufile=sfile)

                fheaders = self.payload['headers']

                # Perform Upload.
                self._putter(conn=conn,
                             fpath=u_file,
                             rpath=rpath,
                             fheaders=fheaders,
                             retry=retry)

                # Put headers on the object if custom headers, or save perms.
                if any([ARGS.get('object_headers') is not None,
                        ARGS.get('save_perms') is not None]):

                    if ARGS.get('object_headers') is not None:
                        fheaders.update(ARGS.get('object_headers'))
                    if ARGS.get('save_perms') is not None:
                        fheaders.update(basic.stat_file(local_file=u_file))

                    self._header_poster(conn=conn,
                                        rpath=rpath,
                                        fheaders=fheaders,
                                        retry=retry)

    def object_deleter(self, url, container, u_file):
        """Deletes an objects in a container.

        :param url:
        :param container:
        :param u_file:
        """
        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count, delay=2, obj=u_file):
            # Open Connection
            conn = http.open_connection(url=url)

            # Open connection and perform operation
            with meth.operation(retry, conn):
                rpath = http.quoter(url=url.path,
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

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count, delay=2, obj=u_file):
            # Open Connection
            conn = http.open_connection(url=url)

            # Perform operation
            with meth.operation(retry, conn):
                fheaders = self.payload['headers']

                rpath = http.quoter(url=url.path,
                                    cont=container,
                                    ufile=u_file)
                # Perform Download.
                self._downloader(conn=conn,
                                 rpath=rpath,
                                 fheaders=fheaders,
                                 lfile=u_file,
                                 source=source,
                                 retry=retry)

    def object_lister(self, url, container, object_count=None, last_obj=None):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :param container:
        :param object_count:
        :param last_obj:
        :return None | list:
        """

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     obj='Object List'):
            # Open Connection
            conn = http.open_connection(url=url)

            # Open connection and perform operation
            with meth.operation(retry, conn):
                # Determine how many files are in the container
                fpath = http.quoter(url=url.path,
                                    cont=container)
                # Make a connection
                resp = self._header_getter(conn=conn,
                                           rpath=fpath,
                                           fheaders=self.payload['headers'],
                                           retry=retry)
                if resp.status == 404:
                    report.reporter(
                        msg='Not found. %s | %s' % (resp.status, resp.msg)
                    )
                    return None, None, None
                else:
                    if object_count is None:
                        head_check = dict(resp.getheaders())
                        object_count = head_check.get(
                            'x-container-object-count'
                        )
                        if object_count:
                            object_count = int(object_count)
                            if not object_count > 0:
                                return None, None, None
                        else:
                            return None, None, None

                    # Set the number of loops that we are going to do
                    return self._list_getter(conn=conn,
                                             count=object_count,
                                             filepath=fpath,
                                             fheaders=self.payload['headers'],
                                             last_obj=last_obj)

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
            if locals().get('tfile') is not None:
                basic.remove_file(tfile)

        def _time_difference(resp, obj):
            if ARGS.get('save_newer') is True:
                # Get the source object last modified time.
                compare_time = resp.getheader('last_modified')
                if compare_time is None:
                    return True
                elif cloud.time_delta(compare_time=compare_time,
                                      lmobj=obj['last_modified']) is True:
                    return False
                else:
                    return True
            else:
                return True

        def _compare(resp, obj):
            if resp.status == 404:
                report.reporter(
                    msg='Target Object %s not found' % obj['name'],
                    prt=False
                )
                return True
            elif resp.getheader('etag') != obj['hash']:
                report.reporter(
                    msg='Checksum Mismatch on Target Object %s' % obj['name'],
                    prt=False,
                    lvl='debug'
                )
                return _time_difference(resp, obj)
            else:
                return False

        fheaders = self.payload['headers']
        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=5,
                                     obj=obj['name']):
            # Open connection and perform operation
            fmt, date, date_delta, now = basic.time_stamp()
            spath = http.quoter(url=surl.path,
                                cont=scontainer,
                                ufile=obj['name'])
            tpath = http.quoter(url=turl.path,
                                cont=tcontainer,
                                ufile=obj['name'])

            conn = http.open_connection(url=turl)
            with meth.operation(retry, conn=conn, obj=obj):
                resp = self._header_getter(conn=conn,
                                           rpath=tpath,
                                           fheaders=fheaders,
                                           retry=retry)

                # If object comparison is True GET then PUT object
                if _compare(resp=resp, obj=obj) is not True:
                    return None
            try:
                # Open Connection for source Download
                conn = http.open_connection(url=surl)
                with meth.operation(retry,
                                    conn=conn,
                                    obj=obj):

                    # make a temp file.
                    tfile = basic.create_tmp()

                    # Make a connection
                    resp = self._header_getter(conn=conn,
                                               rpath=spath,
                                               fheaders=fheaders,
                                               retry=retry)
                    sheaders = dict(resp.getheaders())

                    # TODO(kevin) add the ability to short upload if timestamp
                    # TODO(kevin) ... is newer on the target.
                    # GET remote Object
                    self._downloader(
                        conn=conn,
                        rpath=spath,
                        fheaders=fheaders,
                        lfile=tfile,
                        source=None,
                        retry=retry,
                        skip=True
                    )

                for nretry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                              delay=5,
                                              obj=obj):
                    # open connection for target upload.
                    conn = http.open_connection(url=turl)
                    with meth.operation(retry,
                                        conn=conn,
                                        obj=obj,
                                        cleanup=_cleanup):
                        resp = self._header_getter(conn=conn,
                                                   rpath=tpath,
                                                   fheaders=fheaders,
                                                   retry=nretry)

                        self.resp_exception(resp=resp, rty=nretry)
                        # PUT remote object
                        self._putter(conn=conn,
                                     fpath=tfile,
                                     rpath=tpath,
                                     fheaders=fheaders,
                                     retry=nretry,
                                     skip=True)

                        # let the system rest for 3 seconds.
                        basic.stupid_hack(wait=3)

                        # With the source headers POST new headers on target
                        if ARGS.get('clone_headers') is True:
                            resp = self._header_getter(conn=conn,
                                                       rpath=tpath,
                                                       fheaders=fheaders,
                                                       retry=nretry)
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
                                retry=nretry
                            )
            finally:
                _cleanup()
