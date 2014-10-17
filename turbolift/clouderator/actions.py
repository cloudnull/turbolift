# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import urllib
import urlparse

import cloudlib
from cloudlib import http
from cloudlib import logger
from cloudlib import shell
from requests import exceptions as requests_exp

from turbolift import exceptions
from turbolift.authentication import auth
from turbolift.clouderator import utils as cloud_utils


LOG = logger.getLogger('turbolift')


def quoter(obj):
    """Return a Quoted URL.

    :param obj: ``basestring``
    :return: ``str``
    """

    return urllib.quote(cloud_utils.ustr(obj=obj))


class CloudActions(object):
    def __init__(self, job_args):
        """

        :param job_args:
        """
        self.job_args = job_args
        self.http = http.MakeRequest()
        self.shell = shell.ShellCommands(
            log_name='turbolift', debug=self.job_args.get('debug')
        )

    def _return_base_data(self, url, container, container_object=None,
                          container_headers=None, object_headers=None):
        """Return headers and a parsed url.

        :param url:
        :param container:
        :param container_object:
        :param container_headers:
        :return: ``tuple``
        """
        headers = self.job_args['base_headers']
        headers.update({'X-Auth-Token': self.job_args['os_token']})

        _container_uri = url.geturl().rstrip('/')

        if container:
            _container_uri = '%s/%s' % (
                _container_uri, quoter(container)
            )

        if container_object:
            _container_uri = '%s/%s' % (
                _container_uri, quoter(container_object)
            )

        if object_headers:
            headers.update(object_headers)

        if container_headers:
            headers.update(container_headers)

        return headers, urlparse.urlparse(_container_uri)

    @cloud_utils.retry(requests_exp.ReadTimeout)
    def _putter(self, uri, headers, local_object=None):
        """Place  object into the container.

        :param uri:
        :param headers:
        :param local_object:
        """

        if local_object:
            with open(local_object, 'rb') as f_open:
                resp = self.http.put(url=uri, body=f_open, headers=headers)
        else:
            resp = self.http.put(url=uri, headers=headers)

        return self._resp_exception(resp=resp)

    @cloud_utils.retry(requests_exp.ReadTimeout)
    def _deleter(self, uri, headers):
        """Perform HEAD request on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        # perform Object HEAD request
        resp = self.http.delete(url=uri, headers=headers)
        self._resp_exception(resp=resp)
        return resp

    @cloud_utils.retry(requests_exp.ReadTimeout)
    def _header_getter(self, uri, headers):
        """Perform HEAD request on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        # perform Object HEAD request
        resp = self.http.head(url=uri, headers=headers)
        self._resp_exception(resp=resp)
        return resp

    @cloud_utils.retry(requests_exp.ReadTimeout)
    def _header_poster(self, uri, headers):
        """POST Headers on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        resp = self.http.post(url=uri, body=None, headers=headers)
        self._resp_exception(resp=resp)
        return resp

    @staticmethod
    def _last_marker(base_path, last_object):
        """Set Marker.

        :param base_path:
        :param last_object:
        :return str:
        """

        return '%s&marker=%s' % (base_path, last_object)

    def _obj_index(self, uri, base_path, marked_path, headers):
        """

        :param uri:
        :param base_path:
        :param marked_path:
        :param headers:
        :return:
        """
        object_list = list()
        l_obj = None
        container_uri = uri.geturl()

        while True:
            marked_uri = urlparse.urljoin(container_uri, marked_path)
            resp = self.http.get(url=marked_uri, headers=headers)
            self._resp_exception(resp=resp)
            return_list = resp.json()

            time_offset = self.job_args.get('time_offset')
            for obj in return_list:
                if time_offset is not None:
                    # Get the last_modified data from the Object.
                    time_delta = cloud_utils.TimeDelta(
                        job_args=self.job_args,
                        last_modified=time_offset
                    )
                    if time_delta is True:
                        object_list.append(obj)
                else:
                    object_list.append(obj)

            if object_list:
                last_obj_in_list = object_list[-1].get('name')
            else:
                last_obj_in_list = None

            if l_obj == last_obj_in_list:
                return object_list
            else:
                l_obj = last_obj_in_list
                marked_path = self._last_marker(
                    base_path=base_path,
                    last_object=l_obj
                )

    def _list_getter(self, uri, headers, last_obj=None):
        """Get a list of all objects in a container.

        :param uri:
        :param headers:
        :return list:
        """

        # Quote the file path.
        base_path = marked_path = (
            '%s/?limit=10000&format=json' % cloud_utils.ustr(uri.path)
        )

        if last_obj:
            marked_path = self._last_marker(
                base_path=base_path,
                last_object=quoter(last_obj)
            )

        file_list = self._obj_index(
            uri,
            base_path,
            marked_path,
            headers
        )
        final_list = cloud_utils.unique_list_dicts(dlist=file_list, key='name')
        LOG.debug('Found [ %d ] entries(s)', len(final_list))
        return final_list

    def _resp_exception(self, resp):
        """If we encounter an exception in our upload.

        we will look at how we can attempt to resolve the exception.

        :param resp:
        """

        message = [
            'Url: [ %s ] Reason: [ %s ] Request: [ %s ] Status Code: [ %s ]. ',
            resp.url,
            resp.reason,
            resp.request,
            resp.status_code
        ]

        # Check to make sure we have all the bits needed
        if not hasattr(resp, 'status_code'):
            message[0] += 'No Status to check. Turbolift will retry...'
            raise exceptions.SystemProblem(message)
        elif resp is None:
            message[0] += 'No response information. Turbolift will retry...'
            raise exceptions.SystemProblem(message)
        elif resp.status_code == 401:
            message[0] += (
                'Turbolift experienced an Authentication issue. Turbolift'
                ' will retry...'
            )
            self.job_args.update(auth.authenticate(self.job_args))
            raise exceptions.SystemProblem(message)
        elif resp.status_code == 404:
            message[0] += 'Item not found.'
            LOG.debug(*message)
        elif resp.status_code == 409:
            message[0] += (
                'Request Conflict. Turbolift is abandoning this...'
            )
        elif resp.status_code == 413:
            return_headers = resp.headers
            retry_after = return_headers.get('retry_after', 10)
            cloud_utils.stupid_hack(wait=retry_after)
            message[0] += (
                'The System encountered an API limitation and will'
                ' continue in [ %s ] Seconds' % retry_after
            )
            raise exceptions.SystemProblem(message)
        elif resp.status_code == 502:
            message[0] += (
                'Failure making Connection. Turbolift will retry...'
            )
            raise exceptions.SystemProblem(message)
        elif resp.status_code == 503:
            cloud_utils.stupid_hack(wait=10)
            message[0] += 'SWIFT-API FAILURE'
            raise exceptions.SystemProblem(message)
        elif resp.status_code == 504:
            cloud_utils.stupid_hack(wait=10)
            message[0] += 'Gateway Failure.'
            raise exceptions.SystemProblem(message)
        elif resp.status_code >= 300:
            message[0] += 'General exception.'
            raise exceptions.SystemProblem(message)
        else:
            LOG.debug(*message)

    @cloud_utils.retry(exceptions.SystemProblem)
    def list_items(self, url, container=None, last_obj=None):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :param container:
        :param last_obj:
        :return None | list:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container
        )

        if container:
            resp = self._header_getter(uri=container_uri, headers=headers)
            if resp.status_code == 404:
                LOG.warn('Container [ %s ] not found.', container)
                return [resp]

        return self._list_getter(
            uri=container_uri,
            headers=headers,
            last_obj=last_obj
        )

    @cloud_utils.retry(exceptions.SystemProblem)
    def show_details(self, url, container, container_object=None):
        """Return Details on an object or container.

        :param url:
        :param container:
        :param container_object:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object
        )

        return self._header_getter(
            uri=container_uri,
            headers=headers
        )

    @cloud_utils.retry(exceptions.SystemProblem)
    def update_object(self, url, container, container_object, object_headers,
                      container_headers):
        """Update an existing object in a swift container.

        This method will place new headers on an existing object or container.

        :param url:
        :param container:
        :param container_object:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object,
            container_headers=container_headers,
            object_headers=object_headers,
        )

        return self._header_poster(
            uri=container_uri,
            headers=headers
        )

    @cloud_utils.retry(exceptions.SystemProblem)
    def container_cdn_command(self, url, container, container_object,
                              cdn_headers):
        """Command your CDN enabled Container.

        :param url:
        :param container:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object,
            object_headers=cdn_headers
        )

        if self.job_args.get('purge'):
            return self._deleter(
                uri=container_uri,
                headers=headers
            )
        else:
            return self._header_poster(
                uri=container_uri,
                headers=headers
            )

    @cloud_utils.retry(exceptions.SystemProblem)
    def put_container(self, url, container, container_headers=None):
        """Create a container if it is not Found.

        :param url:
        :param container:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_headers=container_headers
        )

        resp = self._header_getter(
            uri=container_uri,
            headers=headers
        )
        if resp.status_code == 404:
            return self._putter(uri=container_uri, headers=headers)
        else:
            return resp

    @cloud_utils.retry(exceptions.SystemProblem)
    def put_object(self, url, container, container_object, local_object,
                   object_headers, meta=None):
        """This is the Sync method which uploads files to the swift repository

        if they are not already found. If a file "name" is found locally and
        in the swift repository an MD5 comparison is done between the two
        files. If the MD5 is miss-matched the local file is uploaded to the
        repository. If custom meta data is specified, and the object exists the
        method will put the metadata onto the object.

        :param url:
        :param container:
        :param container_object:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object,
            container_headers=object_headers,
            object_headers=meta
        )

        if self.job_args.get('sync'):
            resp = self._header_getter(
                uri=container_uri,
                headers=headers
            )

            if resp.status_code == 200:
                try:
                    self.shell.md5_checker(
                        md5sum=resp.headers.get('etag'),
                        local_file=local_object
                    )
                except cloudlib.MD5CheckMismatch:
                    pass
                else:
                    return resp

        return self._putter(
            uri=container_uri,
            headers=headers,
            local_object=local_object
        )


    @cloud_utils.retry(exceptions.SystemProblem)
    def delete_items(self, url, container, container_object=None):
        """Deletes an objects in a container.

        :param url:
        :param container:
        :param u_file:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object
        )

        resp = self._header_getter(
            uri=container_uri,
            headers=headers
        )

        if resp.status_code != 404:
            return self._deleter(uri=container_uri, headers=headers)
        else:
            return resp


class CloudActionsOld(object):
    def __init__(self, payload):
        self.payload = payload

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
