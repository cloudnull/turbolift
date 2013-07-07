# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import sys
import time
import json
import hashlib
import httplib
import traceback
from urllib import quote
from turbolift.operations import generators as gen


class AuthenticationProblem(Exception):
    pass


class SystemProblem(Exception):
    pass


class NovaAuth(object):
    def __init__(self, tur_arg, work_q=None):
        """
        NovaAuth is a class that handels all aspects of the turbolift
        experience Here you will be able to authenticate agains the API, create
        containers and upload content
        """
        self.tur_arg = tur_arg
        self.work_q = work_q
        self.retry_atmp = self.tur_arg.get('error_retry', 1)

    def response_type(self):
        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   timeout=960,
                                   delay=5):
            try:
                # Compatibility with Python 2.6
                if sys.version_info < (2, 7, 0):
                    resp = self.conn.getresponse()
                else:
                    resp = self.conn.getresponse(buffering=True)
            except httplib.BadStatusLine:
                self.connection_prep(conn_close=True)
                retry()
            else:
                return resp, True

    def result_exception(self, resp, headers, authurl, jsonreq=None):
        """
        If we encounter an exception in our upload, we will look at how we
        can attempt to resolve the exception.
        """
        try:
            if any([resp.status == 401, resp.status is None]):
                print('MESSAGE\t: Forced Re-authentication is happening.')
                time.sleep(2)
                self.connection_prep(conn_close=True)
                reqjson, auth_url = self.osauth()
                self.make_request(jsonreq=reqjson, url=auth_url)
                raise SystemProblem('NOVA-API AUTH FAILURE -> REQUEST:'
                                    ' %s %s %s %s' % (resp.status,
                                                      resp.reason,
                                                      jsonreq,
                                                      authurl))
            elif resp.status == 413:
                _di = dict(resp.getheaders())
                time.sleep(int(_di.get('retry_after', 5)))
                self.connection_prep(conn_close=True)
                raise SystemProblem('The System encountered an API limitation'
                                    ' and will continue in %s Seconds'
                                    % _di.get('retry_after', 5))
            elif resp.status == 502:
                self.connection_prep(conn_close=True, http=True)
                raise SystemProblem('Failure using HTTPS, Changing to HTTP')
            elif resp.status >= 300:
                self.connection_prep(conn_close=True)
                raise SystemProblem('NOVA-API FAILURE -> REQUEST: %s %s %s %s'
                                    % (resp.status,
                                       resp.reason,
                                       authurl,
                                       jsonreq))
        except SystemProblem, exp:
            print(exp)
            return True
        except Exception, exp:
            sys.exit(exp)
        else:
            return False

    def connection_prep(self, conn_close=None, http=None):
        """
        After authentication, the connection_prep method opens a socket
        to the cloud files endpoint.
        """
        if conn_close is True:
            self.conn.close()
        else:
            self.headers = self.tur_arg['base_headers']
            self.url_data = self.tur_arg['simple_endpoint'].split('/')
            self.url = self.url_data[0]
            self.c_path = quote('/%s' % ('/'.join(self.url_data[1:])))

        if http is None:
            self.conn = httplib.HTTPSConnection(self.url)
        else:
            print('Attempting HTTP connection')
            self.conn = httplib.HTTPConnection(self.url)

        if self.tur_arg['os_verbose']:
            print('connecting to the API for %s ==> %s %s' % (self.c_path,
                                                              self.headers,
                                                              self.c_path))
            self.conn.set_debuglevel(1)
        return self.conn

    def osauth(self):
        """
        Authentication For Openstack API, Pulls the full Openstack Service
        Catalog Credentials are the Users API Username and Key/Password
        "osauth" has a Built in Rackspace Method for Authentication

        Set a DC Endpoint and Authentication URL for the Open Stack environment
        """
        if any([self.tur_arg['os_rax_auth'] == 'LON']):
            self.tur_arg['os_region'] = self.tur_arg.get('os_rax_auth')
            if self.tur_arg['os_auth_url']:
                authurl = self.tur_arg.get('os_auth_url')
            else:
                authurl = 'lon.identity.api.rackspacecloud.com'
        elif any([self.tur_arg['os_rax_auth'] == 'DFW',
                  self.tur_arg['os_rax_auth'] == 'ORD',
                  self.tur_arg['os_rax_auth'] == 'SYD']):
            self.tur_arg['os_region'] = self.tur_arg.get('os_rax_auth')
            if self.tur_arg.get('os_auth_url'):
                authurl = self.tur_arg.get('os_auth_url')
            else:
                authurl = 'identity.api.rackspacecloud.com'
        else:
            if not self.tur_arg['os_region']:
                sys.exit('FAIL\t: You have to specify '
                         'a Region along with an Auth URL')
            if self.tur_arg['os_auth_url']:
                authurl = self.tur_arg.get('os_auth_url')
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
            authurl = self.tur_arg.get('os_auth_url')
        jsonreq = json.dumps({'auth': {prefix: setup}})

        # remove the prefix for the Authentication URL
        authurl = authurl.strip('http?s://')
        url_data = authurl.split('/')
        url = url_data[0]
        return jsonreq, url

    def make_request(self, jsonreq, url):
        for retry in gen.retryloop(attempts=self.retry_atmp,
                                   timeout=960,
                                   delay=5):
            conn = httplib.HTTPSConnection(url)

            if self.tur_arg['os_verbose']:
                print('JSON REQUEST: %s' % jsonreq)
                conn.set_debuglevel(1)

            headers = {'Content-Type': 'application/json'}
            tokenurl = '/%s/tokens' % self.tur_arg.get('os_version')
            conn.request('POST', tokenurl, jsonreq, headers)

            try:
                # Compatibility with Python 2.6
                if sys.version_info < (2, 7, 0):
                    resp = conn.getresponse()
                else:
                    resp = conn.getresponse(buffering=True)
            except httplib.BadStatusLine:
                conn.close()
                retry()

            readresp = resp.read()
            jrp = json.loads(readresp)
            conn.close()

            # Check that the status was a good one
            if resp.status >= 500:
                print('Attempting HTTP connection')
                conn = httplib.HTTPConnection(url)
                retry()
            elif self.result_exception(resp=resp,
                                       headers=self.headers,
                                       authurl=self.url,
                                       jsonreq=self.c_path):
                retry()
            else:
                if self.tur_arg['os_verbose']:
                    print('JSON decoded and pretty')
                    print json.dumps(jrp, indent=2)
            # Send Response to Parser
            return self.parse_request(json_response=jrp)

    def parse_request(self, json_response):
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
                raise AuthenticationProblem('No Endpoint Found')

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
        """
        container_name = 'The name of the Container'
        Enable the CDN on a provided Container. If custom meta data is
        specified, and the container exists the
        method will put the metadata onto the object.
        """
        cdnurl_data = self.tur_arg['simple_cdn_endpoint'].split('/')
        cdnurl = cdnurl_data[0]
        cdn_path = quote('/%s' % ('/'.join(cdnurl_data[1:])))

        r_loc = '%s/%s' % (cdn_path, container_name)
        path = quote(r_loc)
        c_headers = self.headers
        c_headers.update({'X-CDN-Enabled': True,
                          'X-TTL': self.tur_arg['cdn_ttl'],
                          'X-Log-Retention': self.tur_arg['cdn_logs']})
        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            try:
                conn = httplib.HTTPSConnection(cdnurl)
                conn.request('PUT', path, headers=c_headers)
                resp, check = self.response_type()
                if check is not True:
                    rty()
                else:
                    resp.read()
                if self.tur_arg['os_verbose']:
                    print('ENABLING CDN ON CONTAINER: %s %s %s'
                          % resp.status, resp.reason, container_name)
                if self.result_exception(resp=resp,
                                         headers=c_headers,
                                         authurl=cdnurl,
                                         jsonreq=path):
                    retry()
            except Exception, exp:
                print('ERROR\t: Shits broke son, here comes the'
                      ' stack trace:\t %s' % (sys.exc_info()[1]))
                print exp
            finally:
                conn.close()

    def container_check(self, container_name):
        """
        container_name = 'The name of the Container'
        check a container to see if it exists
        """
        self.connection_prep()
        r_loc = '%s/%s' % (self.c_path, container_name)
        path = quote(r_loc)
        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            c_headers = self.headers
            # Check to see if the container exists
            self.conn.request('HEAD', path, headers=c_headers)
            resp, check = self.response_type()
            if check is not True:
                retry()
            else:
                resp.read()
            # Check that the status was a good one
            if resp.status == 404:
                print('Container Not Found')
            elif self.result_exception(resp=resp,
                                       headers=c_headers,
                                       authurl=self.url,
                                       jsonreq=path):
                retry()
            return resp

    def container_create(self, container_name):
        """
        container_name = 'The name of the Container'
        Create a container if the container specified on the command
        line did not already exist. If custom meta data is specified,
        and the container exists the method will put the metadata
        onto the object.
        """
        r_loc = '%s/%s' % (self.c_path, container_name)
        path = quote(r_loc)
        try:
            for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
                c_headers = self.headers
                if self.tur_arg['container_headers']:
                    c_headers.update(self.tur_arg['container_headers'])

                resp = self.container_check(container_name)
                status_codes = (resp.status, resp.reason, container_name)

                # Check that the status was a good one
                if resp.status == 404:
                    print('Creating Container ==> %s' % container_name)
                    self.conn.request('PUT', path, headers=c_headers)
                    resp, check = self.response_type()
                    if not check is True:
                        retry()
                    else:
                        resp.read()
                    if resp.status == 404:
                        print('Container Not Found %s' % resp.status)
                    elif self.result_exception(resp=resp,
                                               headers=c_headers,
                                               authurl=self.url,
                                               jsonreq=path):
                        retry()
                    status_codes = (resp.status, resp.reason, container_name)
                    if self.tur_arg['os_verbose']:
                        print('CREATING CONTAINER: %s %s %s' % status_codes)
                elif self.result_exception(resp=resp,
                                           headers=c_headers,
                                           authurl=self.url,
                                           jsonreq=path):
                    retry()
                else:
                    if self.tur_arg['os_verbose']:
                        print('Container Found %s %s %s' % status_codes)

                    # Put headers on the object if custom headers used
                    if self.tur_arg['object_headers']:
                        self.conn.request('POST', path, headers=c_headers)

                        resp, check = self.response_type()
                        if check is not True:
                            retry()
                        else:
                            resp.read()

                        if self.result_exception(resp=resp,
                                                 headers=c_headers,
                                                 authurl=self.url,
                                                 jsonreq=path):
                            retry()
        except Exception, exp:
            print('ERROR\t: Shits broke son, here comes the'
                  ' stack trace:\t %s -> Exception\t: %s'
                  % (sys.exc_info()[1], exp))

    def object_deleter(self, file_path, container):
        """
        container_name = 'The name of the Container'
        check a container to see if it exists
        """
        r_loc = '%s/%s/%s' % (self.c_path, container, file_path)
        path = quote(r_loc)
        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            c_headers = self.headers
            # Check to see if the container exists
            self.conn.request('DELETE', path, headers=c_headers)
            resp, check = self.response_type()
            if check is not True:
                retry()
            else:
                resp.read()
            if self.result_exception(resp=resp,
                                     headers=c_headers,
                                     authurl=self.url,
                                     jsonreq=path):
                retry()
            # Give us more data if we requested it
            if any([self.tur_arg['os_verbose'], self.tur_arg['debug']]):
                print 'INFO\t: %s %s %s' % (resp.status,
                                            resp.reason,
                                            file_path)
                if self.tur_arg['debug']:
                    print 'MESSAGE\t: Delete path = %s ==> %s' % (file_path,
                                                                  container)

    def container_deleter(self, container):
        """
        container_name = 'The name of the Container'
        check a container to see if it exists
        """
        self.connection_prep()
        r_loc = '%s/%s' % (self.c_path, container)
        path = quote(r_loc)
        for retry in gen.retryloop(attempts=self.retry_atmp, delay=5):
            c_headers = self.headers
            # Check to see if the container exists
            self.conn.request('DELETE', path, headers=c_headers)
            resp, check = self.response_type()
            if check is not True:
                retry()
            else:
                resp.read()
            if self.result_exception(resp=resp,
                                     headers=c_headers,
                                     authurl=self.url,
                                     jsonreq=path):
                retry()
            # Give us more data if we requested it
            if any([self.tur_arg['os_verbose'], self.tur_arg['debug']]):
                print 'INFO\t: %s %s %s' % (resp.status,
                                            resp.reason,
                                            container)
                if self.tur_arg['debug']:
                    print 'MESSAGE\t: Delete path = %s' % (container)
        self.connection_prep(conn_close=True)

    def get_object_list(self, container_name):
        """
        Builds a long list of files found in a container
        """
        lastobj = None
        try:
            for retry in gen.retryloop(attempts=self.retry_atmp,
                                       delay=5,
                                       backoff=2):
                try:
                    self.connection_prep()

                    # Set the headers if some custom ones were specified
                    c_headers = self.headers
                    if self.tur_arg['object_headers']:
                        c_headers.update(self.tur_arg['object_headers'])

                    # Determine how many files are in the container
                    r_loc = '%s/%s' % (self.c_path, container_name)
                    filepath = quote(r_loc)
                    self.conn.request('HEAD', filepath, headers=c_headers)

                    resp, check = self.response_type()
                    if check is not True:
                        retry()
                    else:
                        resp.read()
                    if self.result_exception(resp=resp,
                                             headers=c_headers,
                                             authurl=self.url,
                                             jsonreq=filepath):
                        retry()
                    count = int(resp.getheader('X-Container-Object-Count'))

                    # Build the List
                    file_list = []

                    # Set the number of loops that we are going to do
                    jobs = count / 10000 + 1
                    filepath = '%s/?limit=10000&format=json' % filepath
                    filepath_m = filepath
                    f_headers = self.headers
                    f_headers.update({'Content-type': 'application/json'})

                    for _ in xrange(jobs):
                        for nest_rty in gen.retryloop(attempts=self.retry_atmp,
                                                      delay=5):
                            self.conn.request('GET',
                                              filepath,
                                              headers=f_headers)
                            resp, check = self.response_type()
                            if check is not True:
                                retry()
                            if self.result_exception(resp=resp,
                                                     headers=c_headers,
                                                     authurl=self.url,
                                                     jsonreq=filepath):
                                nest_rty()
                            _rr = json.loads(resp.read())
                            for obj in _rr:
                                file_list.append(obj['name'])

                            if count - 10000 > 0:
                                count = count - 10000
                                lastobj = file_list[-1]
                                filepath = '%s&marker=%s' % (filepath_m,
                                                             quote(lastobj))
                    # Give us more data if we requested it
                    if any([self.tur_arg['os_verbose'],
                            self.tur_arg['debug']]):
                        print 'INFO\t: %s %s %s' % (resp.status,
                                                    resp.reason,
                                                    file_list)
                        if self.tur_arg['debug']:
                            print('MESSAGE\t: Path => %s'
                                  % (filepath))
                            print(_rr)
                    self.connection_prep(conn_close=True)
                    return file_list

                except Exception, exp:
                    print exp
                    print traceback.format_exc()
                    print('Exception from within an Download Action')
        except KeyboardInterrupt:
            pass

    def get_downloader(self, file_path, file_name, container):
        """
        This is the simple download Method. There is no file level checking
        at the target. The files are simply downloaded.
        """
        try:
            for retry in gen.retryloop(attempts=self.retry_atmp,
                                       delay=5,
                                       backoff=1):
                try:
                    # Set the headers if some custom ones were specified
                    f_headers = self.headers
                    if self.tur_arg['object_headers']:
                        f_headers.update(self.tur_arg['object_headers'])

                    # Get a file list ready for action
                    r_loc = '%s/%s/%s' % (self.c_path, container, file_path)
                    filepath = quote(r_loc)
                    self.conn.request('GET', filepath, headers=f_headers)
                    resp, check = self.response_type()
                    if check is not True:
                        retry()
                    _rr = resp.read()
                    # Check that the status was a good one
                    if self.result_exception(resp=resp,
                                             headers=f_headers,
                                             authurl=self.url,
                                             jsonreq=filepath):
                        retry()

                    # Open our source file
                    with open(file_name, 'wb') as f_name:
                        f_name.write(_rr)
                    f_name.close()

                    # Give us more data if we requested it
                    if any([self.tur_arg['os_verbose'],
                            self.tur_arg['debug']]):
                        print 'INFO\t: %s %s %s' % (resp.status,
                                                    resp.reason,
                                                    file_name)
                        if self.tur_arg['debug']:
                            print('MESSAGE\t: Upload path = %s ==> %s'
                                  % (file_path, filepath))

                except Exception, exp:
                    print(exp)
                    print('Exception from within an Download Action, placing'
                          ' the failed Download back in Queue')
                    self.work_q.put(file_path)
        except IOError:
            print('ERROR\t: path "%s" does not exist or is a broken symlink'
                  % file_name)
        except ValueError:
            print('ERROR\t: The data for "%s" got all jacked up, so it'
                  ' got skipped' % file_name)
        except KeyboardInterrupt:
            pass

    def put_uploader(self, file_path, file_name, container):
        """
        This is the simple upload Method. There is no file level checking'
        ' at the target. The files are simply uploaded.
        """
        try:
            for retry in gen.retryloop(attempts=self.retry_atmp,
                                       delay=5,
                                       backoff=2):
                try:
                    # Set the headers if some custom ones were specified
                    f_headers = self.headers
                    if self.tur_arg['object_headers']:
                        f_headers.update(self.tur_arg['object_headers'])

                    # Get the path ready for action
                    r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                    filepath = quote(r_loc)

                    # Open our source file
                    with open(file_path, 'rb') as f_path:
                        self.conn.request('PUT', filepath,
                                          body=f_path,
                                          headers=f_headers)
                    f_path.close()
                    resp, check = self.response_type()
                    if check is not True:
                        retry()
                    else:
                        resp.read()

                    # Check that the status was a good one
                    if self.result_exception(resp=resp,
                                             headers=f_headers,
                                             authurl=self.url,
                                             jsonreq=filepath):
                        retry()

                    # Give us more data if we requested it
                    if any([self.tur_arg['os_verbose'],
                            self.tur_arg['debug']]):
                        print('INFO\t: %s %s %s' % (resp.status,
                                                    resp.reason,
                                                    file_name))
                        if self.tur_arg['debug']:
                            print('MESSAGE\t: Upload path = %s ==> %s'
                                  % (file_path, filepath))

                except Exception, exp:
                    print('\nFile Failed to be uploaded %s. Error ==> %s'
                          % (file_path, exp))
        except IOError:
            print('ERROR\t: path "%s" does not exist or is a broken symlink'
                  % file_path)
        except ValueError:
            print('ERROR\t: The data for "%s" got all jacked up,'
                  ' so it got skipped' % file_path)
        except KeyboardInterrupt:
            pass

    def sync_uploader(self, file_path, file_name, container):
        """
        This is the Sync method which uploads files to the swift repository'
        if they are not already found. If a file "name" is found locally and
        in the swift repository an MD5 comparison is done between the two
        files. If the MD5 is miss-matched the local file is uploaded to the
        repository. If custom meta data is specified, and the object exists the
        method will put the metadata onto the object.
        """
        #noinspection PyBroadException
        try:
            for retry in gen.retryloop(attempts=self.retry_atmp,
                                       delay=5):
                try:
                    # Set the headers if some custom ones were specified
                    f_headers = self.headers
                    if self.tur_arg['object_headers']:
                        f_headers.update(self.tur_arg['object_headers'])

                    # Get the path ready for action
                    r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                    filepath = quote(r_loc)

                    self.conn.request('HEAD', filepath, headers=f_headers)

                    resp, check = self.response_type()
                    if check is not True:
                        retry()
                    else:
                        resp.read()

                    if resp.status == 404:
                        with open(file_path, 'rb') as f_path:
                            self.conn.request('PUT',
                                              filepath,
                                              body=f_path,
                                              headers=f_headers)
                        f_path.close()
                        try:
                            # Compatibility with Python 2.6
                            if sys.version_info < (2, 7, 0):
                                resp = self.conn.getresponse()
                            else:
                                resp = self.conn.getresponse(buffering=True)
                        except httplib.BadStatusLine:
                            self.conn.close()
                            self.connection_prep()
                            retry()
                        resp.read()
                        if self.result_exception(resp=resp,
                                                 headers=f_headers,
                                                 authurl=filepath,
                                                 jsonreq=r_loc):
                            retry()

                        if self.tur_arg['verbose']:
                            print 'INFO\t: %s %s %s' % (resp.status,
                                                        resp.reason,
                                                        file_name)
                    elif self.result_exception(resp=resp,
                                               headers=f_headers,
                                               authurl=filepath,
                                               jsonreq=r_loc):
                        retry()
                    else:
                        remotemd5sum = resp.getheader('etag')
                        md5 = hashlib.md5()
                        with open(file_path, 'rb') as f_hash:
                            for chunk in iter(lambda: f_hash.read(
                                    128 * md5.block_size), ''):
                                md5.update(chunk)
                        f_hash.close()
                        localmd5sum = md5.hexdigest()

                        if remotemd5sum != localmd5sum:
                            with open(file_path, 'rb') as f_path:
                                self.conn.request('PUT',
                                                  filepath,
                                                  body=f_path,
                                                  headers=f_headers)
                            f_path.close()
                            resp, check = self.response_type()
                            if check is not True:
                                retry()
                            else:
                                resp.read()
                            if self.result_exception(resp=resp,
                                                     headers=f_headers,
                                                     authurl=filepath,
                                                     jsonreq=r_loc):
                                retry()

                            if self.tur_arg['verbose']:
                                proc_dict = {'lmd5': localmd5sum,
                                             'rmd5': remotemd5sum,
                                             'rs': resp.status,
                                             'rr': resp.reason,
                                             'sjf': file_name}
                                print('MESSAGE\t: CheckSumm Mis-Match %(lmd5)s'
                                      ' != %(rmd5)s\n\t  File Upload : %(rs)s'
                                      ' %(rr)s %(sjf)s' % proc_dict)
                        else:
                            if self.tur_arg['verbose']:
                                print 'MESSAGE\t: CheckSum Match', localmd5sum

                            # Put headers on the object if custom headers
                            if self.tur_arg['object_headers']:
                                self.conn.request('POST',
                                                  filepath,
                                                  headers=f_headers)

                                resp, check = self.response_type()
                                if check is not True:
                                    retry()
                                else:
                                    resp.read()

                                if self.result_exception(resp=resp,
                                                         headers=self.headers,
                                                         authurl=filepath,
                                                         jsonreq=r_loc):
                                    retry()
                except Exception, exp:
                    print('\nFile Failed to be uploaded %s. Error ==> %s'
                          % (file_path, exp))
        except IOError:
            print('ERROR\t: path "%s" does not exist or is a broken symlink'
                  % file_path)
        except ValueError:
            print('ERROR\t: The data for "%s" got all jacked up,'
                  ' so it got skipped' % file_path)
        except KeyboardInterrupt:
            pass
