# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import grp
import hashlib
import io
import os
import pwd

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import cloudlib
from cloudlib import http
from cloudlib import logger
from cloudlib import shell

from turbolift import exceptions
from turbolift.authentication import auth
from turbolift.clouderator import utils as cloud_utils


LOG = logger.getLogger('turbolift')


class CloudActions(object):
    def __init__(self, job_args):
        """

        :param job_args:
        """
        self.job_args = job_args
        self.http = http.MakeRequest()
        self.shell = shell.ShellCommands(
            log_name='turbolift',
            debug=self.job_args.get('debug')
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
                _container_uri, cloud_utils.quoter(container)
            )

        if container_object:
            _container_uri = '%s/%s' % (
                _container_uri, cloud_utils.quoter(container_object)
            )

        if object_headers:
            headers.update(object_headers)

        if container_headers:
            headers.update(container_headers)

        return headers, urlparse.urlparse(_container_uri)

    def _sync_check(self, uri, headers, local_object=None, file_object=None):
        resp = self._header_getter(
            uri=uri,
            headers=headers
        )

        if resp.status_code != 200:
            return True

        try:
            self.shell.md5_checker(
                md5sum=resp.headers.get('etag'),
                local_file=local_object,
                file_object=file_object
            )
        except cloudlib.MD5CheckMismatch:
            return True
        else:
            return False

    @cloud_utils.retry(Exception)
    def _chunk_putter(self, uri, open_file, headers=None):
        """Make many PUT request for a single chunked object.

        Objects that are processed by this method have a SHA256 hash appended
        to the name as well as a count for object indexing which starts at 0.

        To make a PUT request pass, ``url``

        :param uri: ``str``
        :param open_file: ``object``
        :param headers: ``dict``
        """
        count = 0
        dynamic_hash = hashlib.sha256(self.job_args.get('container'))
        dynamic_hash = dynamic_hash.hexdigest()
        while True:
            # Read in a chunk of an open file
            file_object = open_file.read(self.job_args.get('chunk_size'))
            if not file_object:
                break

            # When a chuck is present store it as BytesIO
            with io.BytesIO(file_object) as file_object:
                # store the parsed URI for the chunk
                chunk_uri = urlparse.urlparse(
                    '%s.%s.%s' % (
                        uri.geturl(),
                        dynamic_hash,
                        count
                    )
                )

                # Increment the count as soon as it is used
                count += 1

                # Check if the read chunk already exists
                sync = self._sync_check(
                    uri=chunk_uri,
                    headers=headers,
                    file_object=file_object
                )
                if not sync:
                    continue

                # PUT the chunk
                _resp = self.http.put(
                    url=chunk_uri,
                    body=file_object,
                    headers=headers
                )
                self._resp_exception(resp=_resp)
                LOG.debug(_resp.__dict__)

    @cloud_utils.retry(Exception)
    def _putter(self, uri, headers, local_object=None):
        """Place  object into the container.

        :param uri:
        :param headers:
        :param local_object:
        """

        if not local_object:
            return self.http.put(url=uri, headers=headers)

        with open(local_object, 'rb') as f_open:
            large_object_size = self.job_args.get('large_object_size')
            if not large_object_size:
                large_object_size = 5153960756

            if os.path.getsize(local_object) > large_object_size:
                # Remove the manifest entry while working with chunks
                manifest = headers.pop('X-Object-Manifest')
                # Feed the open file through the chunk process
                self._chunk_putter(
                    uri=uri,
                    open_file=f_open,
                    headers=headers
                )
                # Upload the 0 byte object with the manifest path
                headers.update({'X-Object-Manifest': manifest})
                return self.http.put(url=uri, headers=headers)
            else:
                if self.job_args.get('sync'):
                    sync = self._sync_check(
                        uri=uri,
                        headers=headers,
                        local_object=local_object
                    )
                    if not sync:
                        return None

                return self.http.put(
                    url=uri, body=f_open, headers=headers
                )

    @cloud_utils.retry(Exception)
    def _getter(self, uri, headers, local_object):
        """Perform HEAD request on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        if self.job_args.get('sync'):
            sync = self._sync_check(
                uri=uri,
                headers=headers,
                local_object=local_object
            )
            if not sync:
                return None

        # perform Object HEAD request
        resp = self.http.get(url=uri, headers=headers)
        self._resp_exception(resp=resp)

        # Open our source file and write it
        chunk_size = self.job_args['download_chunk_size']
        with open(local_object, 'wb') as f_name:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f_name.write(chunk)
                    f_name.flush()

        if self.job_args.get('restore_perms'):
            if 'X-Object-Meta-perms' in resp.headers:
                os.chmod(
                    local_object,
                    int(resp.headers['x-object-meta-perms'], 8)
                )

            chown_file = {'uid': -1, 'gid': -1}
            if 'X-Object-Meta-owner' in resp.headers:
                chown_file['uid'] = pwd.getpwnam(
                    resp.headers['X-Object-Meta-owner']
                ).pw_uid
            if 'X-Object-Meta-group' in resp.headers:
                chown_file['gid'] = grp.getgrnam(
                    resp.headers['X-Object-Meta-group']
                ).gr_gid
            os.chown(local_object, *chown_file.values())

        return resp

    @cloud_utils.retry(Exception)
    def _deleter(self, uri, headers):
        """Perform HEAD request on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        # perform Object HEAD request
        resp = self.http.delete(url=uri, headers=headers)
        self._resp_exception(resp=resp)
        return resp

    @cloud_utils.retry(Exception)
    def _header_getter(self, uri, headers):
        """Perform HEAD request on a specified object in the container.

        :param uri: ``str``
        :param headers: ``dict``
        """

        # perform Object HEAD request
        resp = self.http.head(url=uri, headers=headers)
        self._resp_exception(resp=resp)
        return resp

    @cloud_utils.retry(Exception)
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

    def _obj_index(self, uri, base_path, marked_path, headers, spr=False):
        """Return an index of objects from within the container.

        :param uri:
        :param base_path:
        :param marked_path:
        :param headers:
        :param spr: "single page return" Limit the returned data to one page
        :type spr: ``bol``
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
            if spr:
                return return_list

            time_offset = self.job_args.get('time_offset')
            for obj in return_list:
                if time_offset:
                    # Get the last_modified data from the Object.
                    time_delta = cloud_utils.TimeDelta(
                        job_args=self.job_args,
                        last_modified=time_offset
                    )
                    if time_delta:
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

    def _list_getter(self, uri, headers, last_obj=None, spr=False):
        """Get a list of all objects in a container.

        :param uri:
        :param headers:
        :return list:
        :param spr: "single page return" Limit the returned data to one page
        :type spr: ``bol``
        """

        # Quote the file path.
        base_path = marked_path = ('%s?limit=10000&format=json' % uri.path)

        if last_obj:
            marked_path = self._last_marker(
                base_path=base_path,
                last_object=cloud_utils.quoter(last_obj)
            )

        file_list = self._obj_index(
            uri=uri,
            base_path=base_path,
            marked_path=marked_path,
            headers=headers,
            spr=spr
        )

        LOG.debug(
            'Found [ %d ] entries(s) at [ %s ]',
            len(file_list),
            uri.geturl()
        )

        if spr:
            return file_list
        else:
            return cloud_utils.unique_list_dicts(
                dlist=file_list, key='name'
            )

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
    def list_items(self, url, container=None, last_obj=None, spr=False):
        """Builds a long list of objects found in a container.

        NOTE: This could be millions of Objects.

        :param url:
        :param container:
        :param last_obj:
        :param spr: "single page return" Limit the returned data to one page
        :type spr: ``bol``
        :return None | list:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container
        )

        if container:
            resp = self._header_getter(uri=container_uri, headers=headers)
            if resp.status_code == 404:
                LOG.info('Container [ %s ] not found.', container)
                return [resp]

        return self._list_getter(
            uri=container_uri,
            headers=headers,
            last_obj=last_obj,
            spr=spr
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

        return self._putter(
            uri=container_uri,
            headers=headers,
            local_object=local_object
        )

    @cloud_utils.retry(exceptions.SystemProblem)
    def get_items(self, url, container, container_object, local_object):
        """Get an objects from a container.

        :param url:
        :param container:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object
        )

        return self._getter(
            uri=container_uri,
            headers=headers,
            local_object=local_object
        )

    @cloud_utils.retry(exceptions.SystemProblem)
    def get_headers(self, url, container, container_object=None):
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
    def delete_items(self, url, container, container_object=None):
        """Deletes an objects in a container.

        :param url:
        :param container:
        """

        headers, container_uri = self._return_base_data(
            url=url,
            container=container,
            container_object=container_object
        )

        return self._deleter(uri=container_uri, headers=headers)
