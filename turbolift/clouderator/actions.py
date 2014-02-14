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
import turbolift.utils.basic_utils as basic
import turbolift.utils.http_utils as http
import turbolift.utils.report_utils as report

from turbolift.authentication.authentication import get_new_token

from turbolift import ARGS


class CloudActions(object):
    def __init__(self, payload):
        self.payload = payload

    def resp_exception(self, resp):
        """If we encounter an exception in our upload.

        we will look at how we can attempt to resolve the exception.

        :param resp:
        """

        # Check to make sure we have all the bits needed
        if not hasattr(resp, 'status_code'):
            raise turbo.SystemProblem('No Status to check.')
        elif resp is None:
            raise turbo.SystemProblem('No response information.')
        elif resp.status_code == 401:
            report.reporter(
                msg=('Turbolift experienced an Authentication issue.'
                     ' STATUS %s REASON %s REQUEST %s. Turbolift will retry'
                     % (resp.status_code, resp.reason, resp.request)),
                lvl='warn',
                log=True,
                prt=False
            )

            # This was done in this manor due to how manager dicts are proxied
            # related : http://bugs.python.org/issue6766
            headers = self.payload['headers']
            headers['X-Auth-Token'] = get_new_token()
            self.payload['headers'] = headers

            raise turbo.AuthenticationProblem(
                'Attempting to resolve the Authentication issue.'
            )
        elif resp.status_code == 404:
            report.reporter(
                msg=('Not found STATUS: %s, REASON: %s, MESSAGE: %s'
                     % (resp.status_code, resp.reason, resp.request)),
                prt=False,
                lvl='debug'
            )
        elif resp.status_code == 413:
            _di = resp.headers
            basic.stupid_hack(wait=_di.get('retry_after', 10))
            raise turbo.SystemProblem(
                'The System encountered an API limitation and will'
                ' continue in "%s" Seconds' % _di.get('retry_after')
            )
        elif resp.status_code == 502:
            raise turbo.SystemProblem('Failure making Connection')
        elif resp.status_code == 503:
            basic.stupid_hack(wait=10)
            raise turbo.SystemProblem('SWIFT-API FAILURE')
        elif resp.status_code == 504:
            basic.stupid_hack(wait=10)
            raise turbo.SystemProblem('Gateway Time-out')
        elif resp.status_code >= 300:
            raise turbo.SystemProblem(
                'SWIFT-API FAILURE -> REASON %s REQUEST %s' % (resp.reason,
                                                               resp.request)
            )
        else:
            report.reporter(
                msg=('MESSAGE %s %s %s' % (resp.status_code,
                                           resp.reason,
                                           resp.request)),
                prt=False,
                lvl='debug'
            )

    def _checker(self, url, rpath, lpath, fheaders, skip):
        """Check to see if a local file and a target file are different.

        :param url:
        :param rpath:
        :param lpath:
        :param retry:
        :param fheaders:
        :return True|False:
        """

        if skip is True:
            return True
        elif ARGS.get('sync'):
            resp = self._header_getter(url=url,
                                       rpath=rpath,
                                       fheaders=fheaders)
            if resp.status_code == 404:
                return True
            elif cloud.md5_checker(resp=resp, local_f=lpath) is True:
                return True
            else:
                return False
        else:
            return True

    def _downloader(self, url, rpath, fheaders, lfile, source,
                    skip=False):
        """Download a specified object in the container.

        :param url:
        :param rpath:
        :param fheaders:
        :param lfile:
        :param skip:
        """

        resp = None

        if source is None:
            local_f = lfile
        else:
            local_f = basic.jpath(root=source, inode=lfile)

        if self._checker(url, rpath, local_f, fheaders, skip) is True:
            report.reporter(
                msg='Downloading remote %s to local file %s' % (rpath, lfile),
                prt=False,
                lvl='debug',
            )

            # Perform Object GET
            resp = http.get_request(
                url=url, rpath=rpath, headers=fheaders, stream=True
            )
            self.resp_exception(resp=resp)
            local_f = basic.collision_rename(file_name=local_f)

            # Open our source file and write it
            with open(local_f, 'wb') as f_name:
                for chunk in resp.iter_content(chunk_size=2048):
                    if chunk:
                        f_name.write(chunk)
                        f_name.flush()
            resp.close()

        if ARGS.get('restore_perms') is not None:
            # Make a connection
            if resp is None:
                resp = self._header_getter(
                    url=url, rpath=rpath, fheaders=fheaders
                )

            all_headers = resp.headers

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

    def _deleter(self, url, rpath, fheaders):
        """Delete a specified object in the container.

        :param url:
        :param rpath:
        :param fheaders:
        """

        # perform Object Delete
        resp = http.delete_request(url=url, headers=fheaders, rpath=rpath)
        self.resp_exception(resp=resp)

        report.reporter(
            msg=('OBJECT %s MESSAGE %s %s %s'
                 % (rpath, resp.status_code, resp.reason, resp.request)),
            prt=False,
            lvl='debug'
        )

    def _putter(self, url, fpath, rpath, fheaders, skip=False):
        """Place  object into the container.

        :param url:
        :param fpath:
        :param rpath:
        :param fheaders:
        """

        if self._checker(url, rpath, fpath, fheaders, skip) is True:
            report.reporter(
                msg='OBJECT ORIGIN %s RPATH %s' % (fpath, rpath),
                prt=False,
                lvl='debug'
            )

            if basic.file_exists(fpath) is False:
                return None
            else:
                with open(fpath, 'rb') as f_open:
                    resp = http.put_request(
                        url=url, rpath=rpath, body=f_open, headers=fheaders
                    )
                    self.resp_exception(resp=resp)

                report.reporter(
                    msg=('MESSAGE %s %s %s'
                         % (resp.status_code, resp.reason, resp.request)),
                    prt=False,
                    lvl='debug'
                )

    def _list_getter(self, url, filepath, fheaders, last_obj=None):
        """Get a list of all objects in a container.

        :param url:
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

        def _obj_index(b_path, m_path):
            f_list = []
            l_obj = None

            while True:
                resp = http.get_request(
                    url=url, rpath=m_path, headers=fheaders
                )
                self.resp_exception(resp=resp)
                return_list = resp.json()

                for obj in return_list:
                    time_offset = ARGS.get('time_offset')
                    if time_offset is not None:
                        # Get the last_modified data from the Object.
                        if cloud.time_delta(lmobj=time_offset) is True:
                            f_list.append(obj)
                    else:
                        f_list.append(obj)

                last_obj_in_list = f_list[-1].get('name')
                if ARGS.get('max_jobs', ARGS.get('object_index')) is not None:
                    max_jobs = ARGS.get('max_jobs', ARGS.get('object_index'))
                    if max_jobs <= len(f_list):
                        return f_list[:max_jobs]
                    elif l_obj is last_obj_in_list:
                        return f_list
                    else:
                        l_obj = last_obj_in_list
                        m_path = _marker_type(
                            base=b_path, last=last_obj_in_list
                        )
                else:
                    if l_obj is last_obj_in_list:
                        return f_list
                    else:
                        l_obj = last_obj_in_list
                        m_path = _marker_type(
                            base=b_path, last=last_obj_in_list
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
            with meth.operation(retry, obj='%s %s' % (fheaders, filepath)):
                file_list = _obj_index(base_path, marked_path)
                final_list = basic.unique_list_dicts(
                    dlist=file_list, key='name'
                )
                list_count = len(final_list)
                report.reporter(
                    msg='INFO: %d object(s) found' % len(final_list),
                    log=True
                )
                if 'name' in file_list[-1]:
                    return final_list, list_count, file_list[-1]['name']
                else:
                    return final_list, list_count, file_list[-1]

    def _header_getter(self, url, rpath, fheaders):
        """perfrom HEAD request on a specified object in the container.

        :param url:
        :param rpath:
        :param fheaders:
        """

        # perform Object HEAD request
        resp = http.head_request(url=url, headers=fheaders, rpath=rpath)
        self.resp_exception(resp=resp)
        return resp

    def _header_poster(self, url, rpath, fheaders):
        """POST Headers on a specified object in the container.

        :param url:
        :param rpath:
        :param fheaders:
        """

        # perform Object POST request for header update.
        resp = http.post_request(url=url, rpath=rpath, headers=fheaders)
        self.resp_exception(resp=resp)

        report.reporter(
            msg='STATUS: %s MESSAGE: %s REASON: %s' % (resp.status_code,
                                                       resp.request,
                                                       resp.reason),
            prt=False,
            lvl='debug'
        )

        return resp.headers

    def detail_show(self, url):
        """Return Details on an object or container."""

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count,
                                     delay=5,
                                     obj=ARGS.get('container')):
            if ARGS.get('object') is not None:
                rpath = http.quoter(url=url.path,
                                    cont=ARGS.get('container'),
                                    ufile=ARGS.get('object'))
            else:
                rpath = http.quoter(url=url.path,
                                    cont=ARGS.get('container'))
            fheaders = self.payload['headers']
            with meth.operation(retry, obj='%s %s' % (fheaders, rpath)):
                return self._header_getter(url=url,
                                           rpath=rpath,
                                           fheaders=fheaders)

    def container_create(self, url, container):
        """Create a container if it is not Found.

        :param url:
        :param container:
        """

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count,
                                     delay=5,
                                     obj=container):

            rpath = http.quoter(url=url.path,
                                cont=container)

            fheaders = self.payload['headers']
            with meth.operation(retry, obj='%s %s' % (fheaders, rpath)):
                resp = self._header_getter(url=url,
                                           rpath=rpath,
                                           fheaders=fheaders)

                # Check that the status was a good one
                if resp.status_code == 404:
                    report.reporter(msg='Creating Container => %s' % container)
                    http.put_request(url=url, rpath=rpath, headers=fheaders)
                    self.resp_exception(resp=resp)
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
            cheaders = self.payload['headers']
            if sfile is not None:
                rpath = http.quoter(url=url.path,
                                    cont=container,
                                    ufile=sfile)
                # perform CDN Object DELETE
                adddata = '%s %s' % (cheaders, container)
                with meth.operation(retry, obj=adddata):
                    resp = http.delete_request(
                        url=url, rpath=rpath, headers=cheaders
                    )
                    self.resp_exception(resp=resp)
            else:
                rpath = http.quoter(url=url.path,
                                    cont=container)
                http.cdn_toggle(headers=cheaders)

                # perform CDN Enable PUT
                adddata = '%s %s' % (cheaders, container)
                with meth.operation(retry, obj=adddata):
                    resp = http.put_request(
                        url=url, rpath=rpath, headers=cheaders
                    )
                    self.resp_exception(resp=resp)

            report.reporter(
                msg='OBJECT %s MESSAGE %s %s %s' % (rpath,
                                                    resp.status_code,
                                                    resp.reason,
                                                    resp.request),
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
            fheaders = self.payload['headers']
            rpath = http.quoter(url=url.path, cont=container)
            with meth.operation(retry, obj='%s %s' % (fheaders, container)):
                # Perform delete.
                self._deleter(url=url,
                              rpath=rpath,
                              fheaders=fheaders)

    def container_lister(self, url, last_obj=None):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :return None | list:
        """

        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     obj='Container List'):

            fheaders = self.payload['headers']
            fpath = http.quoter(url=url.path)
            with meth.operation(retry, obj='%s %s' % (fheaders, fpath)):
                resp = self._header_getter(url=url,
                                           rpath=fpath,
                                           fheaders=fheaders)

                head_check = resp.headers
                container_count = head_check.get('x-account-container-count')
                if container_count:
                    container_count = int(container_count)
                    if not container_count > 0:
                        return None
                else:
                    return None

                # Set the number of loops that we are going to do
                return self._list_getter(url=url,
                                         filepath=fpath,
                                         fheaders=fheaders,
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

            # Open connection and perform operation

            # Get the path ready for action
            sfile = basic.get_sfile(ufile=u_file, source=source)

            if ARGS.get('dir'):
                container = '%s/%s' % (container, ARGS['dir'].strip('/'))

            rpath = http.quoter(url=url.path,
                                cont=container,
                                ufile=sfile)

            fheaders = self.payload['headers']
            with meth.operation(retry, obj='%s %s' % (fheaders, u_file)):
                self._putter(url=url,
                             fpath=u_file,
                             rpath=rpath,
                             fheaders=fheaders)

                # Put headers on the object if custom headers, or save perms.
                if any([ARGS.get('object_headers') is not None,
                        ARGS.get('save_perms') is not None]):

                    if ARGS.get('object_headers') is not None:
                        fheaders.update(ARGS.get('object_headers'))
                    if ARGS.get('save_perms') is not None:
                        fheaders.update(basic.stat_file(local_file=u_file))

                    self._header_poster(url=url,
                                        rpath=rpath,
                                        fheaders=fheaders)

    def object_deleter(self, url, container, u_file):
        """Deletes an objects in a container.

        :param url:
        :param container:
        :param u_file:
        """
        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count, delay=2, obj=u_file):
            fheaders = self.payload['headers']
            rpath = http.quoter(url=url.path,
                                cont=container,
                                ufile=u_file)

                # Make a connection
            with meth.operation(retry, obj='%s %s' % (fheaders, rpath)):
                resp = self._header_getter(url=url,
                                           rpath=rpath,
                                           fheaders=fheaders)
                if not resp.status_code == 404:
                    # Perform delete.
                    self._deleter(url=url,
                                  rpath=rpath,
                                  fheaders=fheaders)

    def object_downloader(self, url, container, source, u_file):
        """Download an Object from a Container.

        :param url:
        :param container:
        :param u_file:
        """

        rty_count = ARGS.get('error_retry')
        for retry in basic.retryloop(attempts=rty_count, delay=2, obj=u_file):
            fheaders = self.payload['headers']
            rpath = http.quoter(url=url.path,
                                cont=container,
                                ufile=u_file)
            with meth.operation(retry, obj='%s %s' % (fheaders, u_file)):
                self._downloader(url=url,
                                 rpath=rpath,
                                 fheaders=fheaders,
                                 lfile=u_file,
                                 source=source)

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
            fheaders = self.payload['headers']
            fpath = http.quoter(url=url.path,
                                cont=container)
            with meth.operation(retry, obj='%s %s' % (fheaders, fpath)):
                resp = self._header_getter(url=url,
                                           rpath=fpath,
                                           fheaders=fheaders)
                if resp.status_code == 404:
                    report.reporter(
                        msg='Not found. %s | %s' % (resp.status_code,
                                                    resp.request)
                    )
                    return None, None, None
                else:
                    if object_count is None:
                        object_count = resp.headers.get(
                            'x-container-object-count'
                        )
                        if object_count:
                            object_count = int(object_count)
                            if not object_count > 0:
                                return None, None, None
                        else:
                            return None, None, None

                    # Set the number of loops that we are going to do
                    return self._list_getter(url=url,
                                             filepath=fpath,
                                             fheaders=fheaders,
                                             last_obj=last_obj)

    def object_syncer(self, surl, turl, scontainer, tcontainer, u_file):
        """Download an Object from one Container and the upload it to a target.

        :param surl:
        :param turl:
        :param scontainer:
        :param tcontainer:
        :param u_file:
        """

        def _cleanup():
            """Ensure that our temp file is removed."""
            if locals().get('tfile') is not None:
                basic.remove_file(tfile)

        def _time_difference(obj_resp, obj):
            if ARGS.get('save_newer') is True:
                # Get the source object last modified time.
                compare_time = obj_resp.header.get('last_modified')
                if compare_time is None:
                    return True
                elif cloud.time_delta(compare_time=compare_time,
                                      lmobj=obj['last_modified']) is True:
                    return False
                else:
                    return True
            else:
                return True

        def _compare(obj_resp, obj):
            if obj_resp.status_code == 404:
                report.reporter(
                    msg='Target Object %s not found' % obj['name'],
                    prt=False
                )
                return True
            elif ARGS.get('add_only'):
                report.reporter(
                    msg='Target Object %s already exists' % obj['name'],
                    prt=True
                )
                return False
            elif obj_resp.headers.get('etag') != obj['hash']:
                report.reporter(
                    msg=('Checksum Mismatch on Target Object %s'
                         % u_file['name']),
                    prt=False,
                    lvl='debug'
                )
                return _time_difference(obj_resp, obj)
            else:
                return False

        fheaders = self.payload['headers']
        for retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                     delay=5,
                                     obj=u_file['name']):
            # Open connection and perform operation
            spath = http.quoter(url=surl.path,
                                cont=scontainer,
                                ufile=u_file['name'])
            tpath = http.quoter(url=turl.path,
                                cont=tcontainer,
                                ufile=u_file['name'])

            with meth.operation(retry, obj='%s %s' % (fheaders, tpath)):
                resp = self._header_getter(url=turl,
                                           rpath=tpath,
                                           fheaders=fheaders)

                # If object comparison is True GET then PUT object
                if _compare(resp, u_file) is not True:
                    return None
            try:
                # Open Connection for source Download
                with meth.operation(retry, obj='%s %s' % (fheaders, spath)):
                    # make a temp file.
                    tfile = basic.create_tmp()

                    # Make a connection
                    resp = self._header_getter(url=surl,
                                               rpath=spath,
                                               fheaders=fheaders)
                    sheaders = resp.headers
                    self._downloader(
                        url=surl,
                        rpath=spath,
                        fheaders=fheaders,
                        lfile=tfile,
                        source=None,
                        skip=True
                    )

                for _retry in basic.retryloop(attempts=ARGS.get('error_retry'),
                                              delay=5,
                                              obj=u_file):
                    # open connection for target upload.
                    adddata = '%s %s' % (fheaders, u_file)
                    with meth.operation(_retry, obj=adddata, cleanup=_cleanup):
                        resp = self._header_getter(url=turl,
                                                   rpath=tpath,
                                                   fheaders=fheaders)
                        self.resp_exception(resp=resp)
                        # PUT remote object
                        self._putter(url=turl,
                                     fpath=tfile,
                                     rpath=tpath,
                                     fheaders=fheaders,
                                     skip=True)

                        # let the system rest for 1 seconds.
                        basic.stupid_hack(wait=1)

                        # With the source headers POST new headers on target
                        if ARGS.get('clone_headers') is True:
                            theaders = resp.headers
                            for key in sheaders.keys():
                                if key not in theaders:
                                    fheaders.update({key: sheaders[key]})
                            # Force the SOURCE content Type on the Target.
                            fheaders.update(
                                {'content-type': sheaders.get('content-type')}
                            )
                            self._header_poster(
                                url=turl,
                                rpath=tpath,
                                fheaders=fheaders
                            )
            finally:
                _cleanup()
