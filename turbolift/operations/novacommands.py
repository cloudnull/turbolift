# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import hashlib
import httplib
import json
import sys
import time
import traceback
import urllib
import urlparse
import os

from turbolift.operations import exceptions
from turbolift.operations import generators as gen


class NovaAuth(object):
    """Authenticate and perform actions with the Openstack API."""

    def __init__(self, tur_arg, work_q=None):
        """NovaAuth is a class that handel's all aspects of turbolift.

        Here you will be able to authenticate against the API, create
        containers and upload content
        :param tur_arg:
        :param work_q:
        """

        self.tur_arg = tur_arg
        self.work_q = work_q
        self.retry_atmp = self.tur_arg.get('error_retry', 1)
        self.c_path = None
        self.headers = None
        self.url = None
        self.url_data = None

    def set_headers(self, ctr=False, cdn=False):
        """Set the headers used in the Cloud Files Request.

        :param ctr:
        :param cdn:
        """

        # Set the headers if some custom ones were specified
        headers = self.headers
        if ctr is True:
            if self.tur_arg['container_headers']:
                headers.update(self.tur_arg['container_headers'])
        elif cdn is True:
            headers.update({'X-CDN-Enabled': True,
                            'X-TTL': self.tur_arg.get('cdn_ttl'),
                            'X-Log-Retention': self.tur_arg.get('cdn_logs')})
        else:
            if self.tur_arg['object_headers']:
                headers.update(self.tur_arg['object_headers'])
        return headers

    def response_type(self, conn, mcr=False):
        """Understand the response type and provide for the connection.

        :param mcr:
        :param conn:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   timeout=960,
                                   delay=5):
            try:
                resp = conn.getresponse()
            except httplib.BadStatusLine as exp:
                if mcr is False:
                    retry()
                else:
                    raise exceptions.SystemProblem('Failed to perform Action'
                                                   ' %s' % exp)
            else:
                return resp, True

    def response_get(self, conn, rty, ret_read=False, mcr=False):
        """Get the response information and return it.

        :param conn:
        :param rty:
        :param ret_read:
        :param mcr:
        """

        resp, check = self.response_type(conn=conn, mcr=mcr)
        if check is not True:
            rty()
        else:
            resp_read = resp.read()
            if ret_read is True:
                return resp, resp_read
            else:
                return resp

    def result_exception(self, resp, authurl, jsonreq=None, dfc=None):
        """If we encounter an exception in our upload.

        we will look at how we can attempt to resolve the exception.
        :param resp:
        :param authurl:
        :param jsonreq:
        :param dfc:
        """

        try:
            if any([resp.status == 401, resp.status is None]):
                print('MESSAGE\t: Forced Re-authentication is happening.')
                time.sleep(2)
                reqjson, auth_url = self.osauth()
                self.make_request(jsonreq=reqjson, url=auth_url)
                raise exceptions.SystemProblem('NOVA-API AUTH FAILURE'
                                               ' -> REQUEST: %s %s %s %s'
                                               % (resp.status,
                                                  resp.reason,
                                                  jsonreq,
                                                  authurl))
            elif resp.status == 404 and dfc is True:
                pass
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                time.sleep(int(_di.get('retry_after', 5)))
                raise exceptions.SystemProblem('The System encountered an API'
                                               ' limitation and will continue'
                                               ' in %s Seconds'
                                               % _di.get('retry_after', 5))
            elif resp.status == 502:
                raise exceptions.SystemProblem('Failure using HTTPS, Changing'
                                               ' to HTTP')
            elif resp.status >= 300:
                raise exceptions.SystemProblem('NOVA-API FAILURE'
                                               ' -> REQUEST: %s %s %s %s'
                                               % (resp.status,
                                                  resp.reason,
                                                  authurl,
                                                  jsonreq))
        except exceptions.SystemProblem as exp:
            print(exp)
            return True
        except Exception as exp:
            sys.exit(exp)
        else:
            return False

    def connection(self, url, http=False):
        """Open either an http or https connection for the provided URL

        :param url:
        :param http:
        """

        if http is False:
            conn = httplib.HTTPSConnection(url)
        else:
            conn = httplib.HTTPConnection(url)
        return conn

    def connection_prep(self, http=False):
        """After authentication, this opens a socket to the endpoint.

        :param http:
        """

        self.headers = self.tur_arg['base_headers']
        self.url_data = self.tur_arg['simple_endpoint'].split('/')
        self.url = self.url_data[0]
        self.c_path = urllib.quote('/%s' % ('/'.join(self.url_data[1:])))

        if http is True:
            conn = self.connection(url=self.url, http=True)
        else:
            conn = self.connection(url=self.url)

        if self.tur_arg['os_verbose']:
            print('connecting to the API for %s ==> %s %s' % (self.c_path,
                                                              self.headers,
                                                              self.c_path))
            conn.set_debuglevel(1)
        return conn

    def osauth(self):
        """Authentication For Openstack API.

        This pulls the full Openstack Service Catalog Credentials are the
        Users API Username and Key/Password "osauth" has a Built in
        Rackspace Method for Authentication

        Set a DC Endpoint and Authentication URL for the Open Stack environment
        """

        if any([self.tur_arg['os_rax_auth'] == 'LON']):
            self.tur_arg['os_region'] = self.tur_arg.get('os_rax_auth')
            if self.tur_arg['os_auth_url']:
                aurl = self.tur_arg.get('os_auth_url')
            else:
                aurl = 'lon.identity.api.rackspacecloud.com'
        elif any([self.tur_arg['os_rax_auth'] == 'DFW',
                  self.tur_arg['os_rax_auth'] == 'ORD',
                  self.tur_arg['os_rax_auth'] == 'SYD']):
            self.tur_arg['os_region'] = self.tur_arg.get('os_rax_auth')
            if self.tur_arg.get('os_auth_url'):
                aurl = self.tur_arg.get('os_auth_url')
            else:
                aurl = 'identity.api.rackspacecloud.com'
        else:
            if not self.tur_arg['os_region']:
                sys.exit('FAIL\t: You have to specify '
                         'a Region along with an Auth URL')
            if self.tur_arg['os_auth_url']:
                aurl = self.tur_arg.get('os_auth_url')
            else:
                sys.exit('FAIL\t: You have to specify an Auth URL'
                         ' along with the Region')

        # Setup our Authentication POST
        setup = {'username': self.tur_arg.get('os_user')}
        if any([self.tur_arg.get('os_apikey'),
                self.tur_arg.get('os_rax_auth')]):
            prefix = 'RAX-KSKEY:apiKeyCredentials'
            setup['apiKey'] = self.tur_arg.get('os_apikey')
        else:
            prefix = 'passwordCredentials'
            setup['password'] = self.tur_arg.get('os_password')
            aurl = self.tur_arg.get('os_auth_url')

        jsonreq = json.dumps({'auth': {prefix: setup}})

        # remove the prefix for the Authentication URL
        if any([aurl.startswith('http://'), aurl.startswith('https://')]):
            return jsonreq, urlparse.urlparse(aurl).netloc
        else:
            return jsonreq, aurl.split('/')[0]

    def make_request(self, jsonreq, url):
        """Make an API request.

        :param jsonreq:
        :param url:
        """

        try:
            conn = self.connection(url=url)
            for retry in gen.retryloop(attempts=self.retry_atmp,
                                       timeout=960,
                                       delay=5):
                if self.tur_arg['os_verbose']:
                    print('JSON REQUEST: %s' % jsonreq)
                    conn.set_debuglevel(1)

                headers = {'Content-Type': 'application/json'}
                tokenurl = '/%s/tokens' % self.tur_arg.get('os_version')
                conn.request('POST', tokenurl, jsonreq, headers)
                resp, resp_read = self.response_get(conn=conn,
                                                    rty=retry,
                                                    ret_read=True,
                                                    mcr=True)
                jrp = json.loads(resp_read)

                # Check that the status was a good one
                if resp.status >= 500:
                    print('500 Error => Attempting HTTP connection')
                    conn = self.connection(url=url, http=True)
                    raise exceptions.SystemProblem(resp)
                elif self.result_exception(resp=resp,
                                           authurl=url,
                                           jsonreq=jsonreq):
                    raise exceptions.SystemProblem(resp)
                else:
                    if self.tur_arg['os_verbose']:
                        print('JSON decoded and pretty')
                        print(json.dumps(jrp, indent=2))
        except exceptions.SystemProblem:
            retry()
        else:
            # Send Response to Parser
            return self.parse_request(json_response=jrp)
        finally:
            conn.close()

    def md5_checker(self, resp, local_file):
        """Check for different Md5 in CloudFiles vs Local File.

        If the md5 sum is different, return True else False

        :param resp:
        :param local_file:
        :return True|False:
        """

        def calc_hash():
            """Read the hash.

            :return data_hash.read():
            """

            return data_hash.read(128 * md5.block_size)

        if os.path.isfile(local_file) is True:
            rmd5sum = resp.getheader('etag')
            md5 = hashlib.md5()
            with open(local_file, 'rb') as data_hash:
                for chk in iter(calc_hash, ''):
                    md5.update(chk)
            lmd5sum = md5.hexdigest()
            if rmd5sum != lmd5sum:
                if self.tur_arg['verbose']:
                    print('MESSAGE\t: CheckSumm Mis-Match %(lmd5)s'
                          ' != %(rmd5)s\n\t  File : %(rs)s %(rr)s'
                          ' - Local File %(lf)s' % {'lmd5': lmd5sum,
                                                    'rmd5': rmd5sum,
                                                    'rs': resp.status,
                                                    'rr': resp.reason,
                                                    'lf': local_file})
                return True
            else:
                if self.tur_arg['verbose']:
                    print('MESSAGE\t: CheckSum Match', lmd5sum)
                return False
        else:
            if self.tur_arg['verbose']:
                print('MESSAGE\t: Local File Not Found %s' % local_file)
            return True

    def parse_request(self, json_response):
        """Parse the return from an API request.

        :param json_response:
        """

        try:
            jra = json_response.get('access')
            token = jra.get('token').get('id')
            self.tur_arg['tenantid'] = jra.get('token').get('tenant').get('id')

            scat = jra.pop('serviceCatalog')
            for srv in scat:
                if srv.get('name') in ('cloudFilesCDN', 'cloudFiles'):
                    if srv.get('name') == 'cloudFilesCDN':
                        cdn = srv.get('endpoints')
                    if srv.get('name') == 'cloudFiles':
                        cfl = srv.get('endpoints')
                elif 'swift' in srv.get('name'):
                    cfl = scat.pop(scat.index(srv))

            for srv in cfl:
                if self.tur_arg.get('os_region') in srv.get('region'):
                    internal = srv.get('internalURL')
                    external = srv.get('publicURL')

            for srv in cdn:
                if self.tur_arg.get('os_region') in srv.get('region'):
                    self.tur_arg['CDNendpoint'] = srv.get('publicURL')
                    cdn_split = self.tur_arg['CDNendpoint'].split('//')[1]
                    self.tur_arg['simple_cdn_endpoint'] = cdn_split

            if not cfl and any([internal, external]):
                raise exceptions.AuthenticationProblem('No Endpoint Found')

            if self.tur_arg.get('internal'):
                self.tur_arg['endpoint'] = internal
            else:
                self.tur_arg['endpoint'] = external

            headers = self.tur_arg.get('base_headers')
            headers.update({'X-Auth-Token': token})
            self.tur_arg['base_headers'] = headers

            url_split = self.tur_arg['endpoint'].split('//')[1]
            self.tur_arg['simple_endpoint'] = url_split
            if self.tur_arg['os_verbose']:
                print('SimpleURL\t: %s\nPublicURL\t: %s\nPrivateURL\t: %s\n'
                      % (url_split, external, internal))
            return self.tur_arg
        except (KeyError, IndexError):
            print('Error while getting answers from auth server.'
                  ' Check the endpoint and auth credentials.')

    def enable_cdn(self, container_name):
        """Enable the CDN on a provided Container.

        If custom meta data is specified, and the container exists the method
        will put the metadata onto the object.
        :param container_name: The name of the Container
        """

        cdnurl_data = self.tur_arg['simple_cdn_endpoint'].split('/')
        cdnurl = cdnurl_data[0]
        cdn_path = urllib.quote('/%s' % ('/'.join(cdnurl_data[1:])))
        r_loc = '%s/%s' % (cdn_path, container_name)
        path = urllib.quote(r_loc)
        c_headers = self.set_headers(cdn=True)
        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = self.connection(url=cdnurl)
                conn.request('PUT', path, headers=c_headers)
                resp = self.response_get(conn=conn, rty=retry)
                if self.tur_arg['os_verbose']:
                    print('ENABLING CDN ON CONTAINER: %s %s %s'
                          % (resp.status, resp.reason, container_name))
                if self.result_exception(resp=resp,
                                         authurl=cdnurl,
                                         jsonreq=path):
                    raise exceptions.SystemProblem(resp)
            except exceptions.SystemProblem:
                retry()
            except Exception as exp:
                print('ERROR\t: Shits broke son, here comes the'
                      ' stack trace:\t %s' % traceback.format_exc())
                print(exp)
            finally:
                conn.close()

    def container_check(self, container_name):
        """check a container to see if it exists.

        :param container_name: The name of the Container
        """
        try:
            conn = self.connection_prep()
            r_loc = '%s/%s' % (self.c_path, container_name)
            path = urllib.quote(r_loc)
            for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
                c_headers = self.set_headers()
                # Check to see if the container exists
                conn.request('HEAD', path, headers=c_headers)
                resp = self.response_get(conn=conn, rty=retry)
                # Check that the status was a good one
                if resp.status == 404:
                    print('Container Not Found')
                elif self.result_exception(resp=resp,
                                           authurl=self.url,
                                           jsonreq=path):
                    raise exceptions.SystemProblem(resp)
        except exceptions.SystemProblem:
            retry()
        else:
            return resp
        finally:
            conn.close()

    def container_create(self, container_name):
        """Create a container if the container specified on the command.

        If custom meta data is specified, and the container exists the method
        will put the metadata onto the object.
        :param container_name: The name of the Container
        """

        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = self.connection_prep()
                r_loc = '%s/%s' % (self.c_path, container_name)
                path = urllib.quote(r_loc)
                c_headers = self.set_headers(ctr=True)

                resp = self.container_check(container_name)
                status_codes = (resp.status, resp.reason, container_name)

                # Check that the status was a good one
                if resp.status == 404:
                    print('Creating Container ==> %s' % container_name)
                    conn.request('PUT', path, headers=c_headers)
                    resp = self.response_get(conn=conn, rty=retry)
                    if resp.status == 404:
                        print('Container Not Found %s' % resp.status)
                    elif self.result_exception(resp=resp,
                                               authurl=self.url,
                                               jsonreq=path):
                        raise exceptions.SystemProblem(resp)
                    status_codes = (resp.status, resp.reason, container_name)
                    if self.tur_arg['os_verbose']:
                        print('CREATING CONTAINER: %s %s %s' % status_codes)
                elif self.result_exception(resp=resp,
                                           authurl=self.url,
                                           jsonreq=path):
                    raise exceptions.SystemProblem(resp)
            except exceptions.SystemProblem:
                retry()
            except Exception as exp:
                print('ERROR\t: Shits broke son, here comes the'
                      ' stack trace:\t %s -> Exception\t: %s'
                      % (traceback.format_exc(), exp))
            else:
                if self.tur_arg['os_verbose']:
                    print('Container Found %s %s %s' % status_codes)
                # Put headers on the object if custom headers used
                if self.tur_arg['object_headers']:
                    conn.request('POST', path, headers=c_headers)
                    resp = self.response_get(conn=conn, rty=retry)
                    if self.result_exception(resp=resp,
                                             authurl=self.url,
                                             jsonreq=path):
                        retry()
            finally:
                conn.close()

    def container_deleter(self, container):
        """check a container to see if it exists

        :param container:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = self.connection_prep()
                r_loc = '%s/%s' % (self.c_path, container)
                path = urllib.quote(r_loc)
                c_headers = self.set_headers()
                # Check to see if the container exists
                conn.request('DELETE', path, headers=c_headers)
                resp = self.response_get(conn=conn, rty=retry)
                if self.result_exception(resp=resp,
                                         authurl=self.url,
                                         jsonreq=path,
                                         dfc=True):
                    raise exceptions.SystemProblem(resp)
            except exceptions.SystemProblem:
                retry()
            else:
                # Give us more data if we requested it
                if any([self.tur_arg['os_verbose'], self.tur_arg['debug']]):
                    print('INFO\t: %s %s %s' % (resp.status,
                                                resp.reason,
                                                container))
                    if self.tur_arg['debug']:
                        print('MESSAGE\t: Delete path = %s' % container)
            finally:
                conn.close()

    def object_putter(self, fpath, rpath, fname, fheaders, retry):
        """Place  object into the container.

        :param fpath:
        :param rpath:
        :param fname:
        :param fheaders:
        :param retry:
        """

        try:
            conn = self.connection_prep()
            with open(fpath, 'rb') as fopen:
                conn.request('PUT',
                             rpath,
                             body=fopen,
                             headers=fheaders)
            resp = self.response_get(conn=conn, rty=retry)
            if self.result_exception(resp=resp,
                                     authurl=self.url,
                                     jsonreq=rpath):
                raise exceptions.SystemProblem(resp)
        except exceptions.SystemProblem:
            retry()
        else:
            if self.tur_arg['verbose']:
                print('INFO\t: %s %s %s' % (resp.status,
                                            resp.reason,
                                            fname))
        finally:
            conn.close()

    def object_deleter(self, file_path, container):
        """check a container to see if it exists

        :param file_path:
        :param container:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = self.connection_prep()
                r_loc = '%s/%s/%s' % (self.c_path, container, file_path)
                remote_path = urllib.quote(r_loc)
                f_headers = self.set_headers()
                conn.request('DELETE', remote_path, headers=f_headers)
                resp = self.response_get(conn=conn, rty=retry)
                if self.result_exception(resp=resp,
                                         authurl=self.url,
                                         jsonreq=remote_path,
                                         dfc=True):
                    raise exceptions.SystemProblem(resp)
            except exceptions.SystemProblem:
                retry()
            else:
                # Give us more data if we requested it
                if any([self.tur_arg['os_verbose'], self.tur_arg['debug']]):
                    print('INFO\t: %s %s %s' % (resp.status,
                                                resp.reason,
                                                file_path))
                    if self.tur_arg['debug']:
                        print('MESSAGE\t: Delete path = %s ==> %s'
                              % (file_path, container))
            finally:
                conn.close()

    def get_object_list(self, container_name, lastobj=None):
        """Builds a long list of files found in a container

        :param container_name:
        :param lastobj:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   delay=5,
                                   backoff=2):
            try:
                conn = self.connection_prep()
                f_headers = self.set_headers()

                # Determine how many files are in the container
                r_loc = '%s/%s' % (self.c_path, container_name)
                filepath = urllib.quote(r_loc)
                conn.request('HEAD', filepath, headers=f_headers)

                resp = self.response_get(conn=conn, rty=retry)
                if self.result_exception(resp=resp,
                                         authurl=self.url,
                                         jsonreq=filepath):
                    raise exceptions.SystemProblem(resp)
                count = int(resp.getheader('X-Container-Object-Count'))

                # Build the List
                file_list = []

                # Set the number of loops that we are going to do
                jobs = count / 10000 + 1
                filepath = '%s/?limit=10000&format=json' % filepath
                filepath_m = filepath
                f_headers.update({'Content-type': 'application/json'})

                for _ in xrange(jobs):
                    for nest_rty in gen.retryloop(attempts=self.retry_atmp,
                                                  delay=5):
                        conn.request('GET',
                                     filepath,
                                     headers=f_headers)
                        resp, resp_read = self.response_get(conn=conn,
                                                            rty=retry,
                                                            ret_read=True)
                        if self.result_exception(resp=resp,
                                                 authurl=self.url,
                                                 jsonreq=filepath):
                            raise exceptions.NoSource(resp)
                        _rr = json.loads(resp_read)
                        for obj in _rr:
                            file_list.append(obj['name'])

                        if count - 10000 > 0:
                            count = count - 10000
                            lastobj = file_list[-1]
                            filepath = (
                                '%s&marker=%s' % (filepath_m,
                                                  urllib.quote(lastobj))
                            )
            except exceptions.NoSource:
                nest_rty()
            except exceptions.SystemProblem:
                retry()
            except KeyboardInterrupt:
                pass
            except Exception as exp:
                print('Exception from within an Download Action\n%s\n%s'
                      % (traceback.format_exc(), exp))
            else:
                # Give us more data if we requested it
                if any([self.tur_arg['os_verbose'],
                        self.tur_arg['debug']]):
                    print('INFO\t: %s %s %s' % (resp.status,
                                                resp.reason,
                                                file_list))
                    if self.tur_arg['debug']:
                        print('MESSAGE\t: Path => %s\nMESSAGE\t: %s'
                              % (filepath, _rr))
                return file_list
            finally:
                conn.close()

    def get_downloader(self, file_path, file_name, container):
        """This is the simple download Method.

        There is no file level checking at the target. The files are simply
        downloaded.

        :param file_path:
        :param file_name:
        :param container:
        """

        def get_action(conn, filepath, local_file, headers, url, retry):
            """Get a target file and save it locally.

            :param conn:
            :param filepath:
            :param file_name:
            :param headers:
            :param url:
            :param retry:
            """

            conn.request('GET', filepath, headers=headers)
            resp, resp_read = self.response_get(conn=conn,
                                                rty=retry,
                                                ret_read=True)
            # Check that the status was a good one
            if self.result_exception(resp=resp,
                                     authurl=url,
                                     jsonreq=filepath):
                raise exceptions.SystemProblem(resp)
            # Open our source file and write it
            with open(local_file, 'wb') as f_name:
                f_name.write(resp_read)

            # Give us more data if we requested it
            if self.tur_arg.get('verbose'):
                print('INFO\t: %s %s %s' % (resp.status,
                                            resp.reason,
                                            local_file))
            if self.tur_arg.get('debug'):
                print('MESSAGE\t: Download path = %s ==> %s'
                      % (file_name, filepath))

        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   delay=5,
                                   backoff=1):
            try:
                conn = self.connection_prep()
                f_headers = self.set_headers()
                # Get a file list ready for action
                remote_path = '%s/%s/%s' % (self.c_path, container, file_path)
                filepath = urllib.quote(remote_path)

                if self.tur_arg.get('dl_sync') is True:
                    conn.request('HEAD', remote_path, headers=f_headers)
                    resp = self.response_get(conn=conn, rty=retry)
                    if self.md5_checker(resp=resp,
                                        local_file=file_name) is True:
                        get_action(conn=conn,
                                   filepath=filepath,
                                   local_file=file_name,
                                   headers=f_headers,
                                   url=self.url,
                                   retry=retry)
                else:
                    get_action(conn=conn,
                               filepath=filepath,
                               local_file=file_name,
                               headers=f_headers,
                               url=self.url,
                               retry=retry)

            except exceptions.SystemProblem:
                retry()
            except IOError:
                print('ERROR\t: path "%s" does not exist or is a broken'
                      ' symlink' % file_name)
            except ValueError:
                print('ERROR\t: The data for "%s" got all jacked up, so it'
                      ' got skipped' % file_name)
            except KeyboardInterrupt:
                pass
            except Exception as exp:
                print traceback.format_exc()
                print('ERROR\t: Exception from within an Download Action '
                      'Message == %s' % exp)
            finally:
                conn.close()

    def put_uploader(self, file_path, file_name, container):
        """This is the simple upload Method.

        There is no file level checking at the target.
        The files are simply uploaded.
        :param file_path:
        :param file_name:
        :param container:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   delay=5,
                                   backoff=2):
            try:
                f_headers = self.set_headers()
                # Get the path ready for action
                r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                remote_path = urllib.quote(r_loc)
                self.object_putter(fpath=file_path,
                                   rpath=remote_path,
                                   fname=file_name,
                                   fheaders=f_headers,
                                   retry=retry)
            except IOError:
                print('ERROR\t: path "%s" does not exist or is a broken'
                      ' symlink' % file_path)
            except ValueError:
                print('ERROR\t: The data for "%s" got all jacked up,'
                      ' so it got skipped' % file_path)
            except KeyboardInterrupt:
                pass
            except Exception as exp:
                print('\nFile Failed to be uploaded %s. Error ==> %s\n\n%s'
                      % (file_path, exp, traceback.format_exc()))
            else:
                if self.tur_arg['debug']:
                    print('MESSAGE\t: Upload path = %s ==> %s'
                          % (file_path, remote_path))

    def sync_uploader(self, file_path, file_name, container):
        """This is the Sync method which uploads files to the swift repository

        if they are not already found. If a file "name" is found locally and
        in the swift repository an MD5 comparison is done between the two
        files. If the MD5 is miss-matched the local file is uploaded to the
        repository. If custom meta data is specified, and the object exists the
        method will put the metadata onto the object.

        :param file_path:
        :param file_name:
        :param container:
        """

        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = self.connection_prep()
                f_headers = self.set_headers()

                # Get the path ready for action
                r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                remote_path = urllib.quote(r_loc)
                conn.request('HEAD', remote_path, headers=f_headers)
                resp = self.response_get(conn=conn, rty=retry)
                if any([resp.status == 404,
                        self.md5_checker(resp=resp,
                                         local_file=file_path) is True]):
                    # If different or not found, perform Upload.
                    self.object_putter(fpath=file_path,
                                       rpath=remote_path,
                                       fname=file_name,
                                       fheaders=f_headers,
                                       retry=retry)
            except IOError:
                print('ERROR\t: path "%s" does not exist or is a broken'
                      ' symlink' % file_path)
            except ValueError:
                print('ERROR\t: The data for "%s" got all jacked up,'
                      ' so it got skipped' % file_path)
            except KeyboardInterrupt:
                pass
            except Exception as exp:
                print('\nFile Failed to be uploaded %s. Error ==> %s\n\n%s'
                      % (file_path, exp, traceback.format_exc()))
            else:
                # Put headers on the object if custom headers
                if self.tur_arg['object_headers']:
                    conn.request('POST',
                                 remote_path,
                                 headers=f_headers)
                    resp = self.response_get(conn=conn, rty=retry)
                    if self.result_exception(resp=resp,
                                             authurl=self.url,
                                             jsonreq=remote_path):
                        retry()
            finally:
                conn.close()
