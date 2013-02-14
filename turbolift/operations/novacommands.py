"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""
import sys
import time
import json
import hashlib
import httplib
from urllib import quote

from turbolift.operations import generators


class NovaAuth(object):
    def __init__(self, tur_arg):
        """
        NovaAuth is a class that handels all aspects of the turbolift experience
        Here you will be able to authenticate agains the API, create containers
        and upload content
        """
        self.tur_arg = tur_arg


    def result_exception(self, resp, headers, authurl, jsonreq=None):
        """
        If we encounter an exception in our upload, we will look at how we can attempt
        to resolve the exception.
        """
        try:
            if resp.status == 401 or resp.status == None:
                time.sleep(2)
                print('MESSAGE\t: Forced Re-authentication is happening.')
                sys.exit('Authentication has failed. so we quit')
                self.connection_prep()
                self.os_auth()
                print('NOVA-API AUTH FAILURE -> REQUEST: %s %s %s %s' % (resp.status,
                                                                         resp.reason,
                                                                         jsonreq,
                                                                         authurl))
            elif resp.status == 413:
                status_info = resp.getheaders()
                di = dict(status_info)
                print(di)
                print('The System encountered an API limitation and will continue '
                      'in %s Seconds' % di['retry-after'])
                time.sleep(int(di['retry-after']))
            elif resp.status == 400:
                print 'MESSAGE\t: Opened File Error, re-Opening the Socket to retry.'
            elif resp.status == 502:
                self.connection_prep(http=True)
            else:
                print('NOVA-API FAILURE -> REQUEST: %s %s %s %s' % (resp.status,
                                                                    resp.reason,
                                                                    jsonreq,
                                                                    authurl))
        except Exception, e:
            sys.exit(e)
        finally:
            self.connection_prep()


    def connection_prep(self, conn_close=None, http=None):
        """
        After authentication, the connection_prep method opens a socket to the cloud files endpoint.
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
            print('connecting to the API for %s ==> %s %s' % (self.c_path, self.headers, self.c_path))
            self.conn.set_debuglevel(1)
        return self.conn


    def osauth(self):
        """
        Authentication For Openstack API, Pulls the full Openstack Service Catalog
        Credentials are the Users API Username and Key/Password
        "osauth" has a Built in Rackspace Method for Authentication
        """
        """
        Set a DC Endpoint and Authentication URL for the Open Stack environment
        """
        if self.tur_arg['os_rax_auth'] == 'LON':
            self.tur_arg['os_region'] = self.tur_arg['os_rax_auth']
            if self.tur_arg['os_auth_url']:
                authurl = self.tur_arg['os_auth_url']
            else:
                authurl = 'lon.identity.api.rackspacecloud.com'
        elif self.tur_arg['os_rax_auth'] == 'DFW' or self.tur_arg['os_rax_auth'] == 'ORD':
            self.tur_arg['os_region'] = self.tur_arg['os_rax_auth']
            if self.tur_arg['os_auth_url']:
                authurl = self.tur_arg['os_auth_url']
            else:
                authurl = 'identity.api.rackspacecloud.com'
        else:
            if not self.tur_arg['os_region']:
                sys.exit('FAIL\t: You have to specify '
                         'a Region along with an Auth URL')
            if self.tur_arg['os_auth_url']:
                authurl = self.tur_arg['os_auth_url']
            else:
                sys.exit('FAIL\t: You have to specify an Auth URL along with the Region')
    
        if self.tur_arg['os_apikey'] or self.tur_arg['os_rax_auth']:
            jsonreq = json.dumps({'auth': {'RAX-KSKEY:apiKeyCredentials': {'username': self.tur_arg['os_user'],
                                                                           'apiKey': self.tur_arg['os_apikey']}}})
        else:
            jsonreq = json.dumps({'auth': {'passwordCredentials': {'username': self.tur_arg['os_user'],
                                                                   'password': self.tur_arg['os_password']}}})
            authurl = self.tur_arg['os_auth_url']

        # remove the prefix for the Authentication URL
        authurl = authurl.strip('http?s://')
        url_data = authurl.split('/')
        url = url_data[0]
        for retry in generators.retryloop(attempts=self.tur_arg['error_retry'],
                                          timeout=960,
                                          delay=5):
            conn = httplib.HTTPSConnection(url)
    
            if self.tur_arg['os_verbose']:
                print('JSON REQUEST: %s' % jsonreq)
                conn.set_debuglevel(1)
    
            headers = {'Content-Type': 'application/json'}
            tokenurl = '/%s/tokens' % self.tur_arg['os_version']
            
            conn.request('POST', tokenurl, jsonreq, headers)

            # Compatibility with Python 2.6
            if sys.version_info < (2, 7, 0):
                resp = conn.getresponse()
            else:
                resp = conn.getresponse(buffering=True)

            readresp = resp.read()
            json_response = json.loads(readresp)
            conn.close()
    
            # Check that the status was a good one
            if resp.status == 501:
                print('Attempting HTTP connection')
                conn = httplib.HTTPConnection(url)
                retry()
            elif resp.status >= 300 or resp.status == None:
                self.result_exception(resp=resp,
                                      headers=self.headers,
                                      authurl=self.url,
                                      jsonreq=self.c_path)
                try:
                    retry()
                except Exception, e:
                    print('Authentication has FAILED "%s %s %s %s"' % (resp.status,
                                                                       resp.reason,
                                                                       readresp,
                                                                       e))
                    continue
            else:
                if self.tur_arg['os_verbose']:
                    print('JSON decoded and pretty')
                    print json.dumps(json_response, indent=2)

            try:
                for service in json_response['access']['serviceCatalog']:
                    if service['name'] == 'cloudFiles':
                        for endpoint in service['endpoints']:
                            if endpoint['region'] == self.tur_arg['os_region']:
                                self.tur_arg['endpoint'] = endpoint['publicURL']
                    elif service['name'] == 'swift':
                        for endpoint in service['endpoints']:
                            if endpoint['region'] == self.tur_arg['os_region']:
                                self.tur_arg['endpoint'] = endpoint['publicURL']
                    if service['name'] == 'cloudFilesCDN':
                        for endpoint in service['endpoints']:
                            if endpoint['region'] == self.tur_arg['os_region']:
                                self.tur_arg['CDNendpoint'] = endpoint['publicURL']
        
                self.tur_arg['tenantid'] = json_response['access']['token']['tenant']['id']
                token = json_response['access']['token']['id']
                headers = self.tur_arg['base_headers']
                headers.update({'X-Auth-Token':token})
                self.tur_arg['base_headers'] = headers
                self.tur_arg['simple_cdn_endpoint'] = self.tur_arg['CDNendpoint'].encode('utf8').split('//')[1]
                self.tur_arg['simple_endpoint'] = self.tur_arg['endpoint'].encode('utf8').split('//')[1]
        
                if self.tur_arg['os_verbose']:
                    print('SimpleURL\t: %s'
                          '\nPublicURL\t: %s'
                          '\nTenant\t\t: %s'
                          '\nCDN_manage\t: %s' % (self.tur_arg['simple_endpoint'],
                                                  self.tur_arg['endpoint'],
                                                  self.tur_arg['tenantid'],
                                                  self.tur_arg['CDNendpoint']))

                return self.tur_arg
            except (KeyError, IndexError):
                print 'Error while getting answers from auth server.\nCheck the endpoint and auth credentials.'


    def enable_cdn(self, container_name):
        """
        container_name = 'The name of the Container'
        Enable the CDN on a provided Container. If custom meta data is specified, and the container exists the
        method will put the metadata onto the object.
        """
        cdnurl_data = self.tur_arg['simple_cdn_endpoint'].split('/')
        cdnurl = cdnurl_data[0]
        cdn_path = quote('/%s' % ('/'.join(cdnurl_data[1:])))
        conn = httplib.HTTPSConnection(cdnurl)
        
        r_loc = '%s/%s' % (cdn_path, container_name)
        path = quote(r_loc)
        c_headers = self.headers
        c_headers.update({'X-CDN-Enabled':True,
                          'X-TTL':self.tur_arg['cdn_ttl'],
                          'X-Log-Retention':self.tur_arg['cdn_logs']})
        for retry in generators.retryloop(attempts=self.tur_arg['error_retry'], delay=5):
            try:
                for retry in generators.retryloop(attempts=self.tur_arg['error_retry'], delay=5):
                    conn.request('PUT', path, headers=c_headers)
                    

                    # Compatibility with Python 2.6
                    if sys.version_info < (2, 7, 0):
                        resp = conn.getresponse()
                    else:
                        resp = conn.getresponse(buffering=True)

                    resp.read()
                    status_codes = (resp.status, resp.reason, container_name)
                    if self.tur_arg['os_verbose']:
                        print('ENABLING CDN ON CONTAINER: %s %s %s' % status_codes)
                    if resp.status >= 300 or resp.status == None:
                        print('Failure happened, will retry %s %s %s' % status_codes)
                        retry() ; continue
            except Exception, e:
                print 'ERROR\t: Shits broke son, here comes the stack trace:\t %s' % (sys.exc_info()[1])
                print e
            finally:
                conn.close()

    def container_create(self, container_name):
        """
        container_name = 'The name of the Container'
        Create a container if the container specified on the command line did not already exist.
        If custom meta data is specified, and the container exists the method will put the metadata
        onto the object.
        """
        r_loc = '%s/%s' % (self.c_path, container_name)
        path = quote(r_loc)
        try:
            for retry in generators.retryloop(attempts=self.tur_arg['error_retry'], delay=5):
                c_headers = self.headers
                if self.tur_arg['container_headers']:
                    c_headers.update(self.tur_arg['container_headers'])

                # Check to see if the container exists
                self.conn.request('HEAD', path, headers=c_headers)

                # Compatibility with Python 2.6
                if sys.version_info < (2, 7, 0):
                    resp = self.conn.getresponse()
                else:
                    resp = self.conn.getresponse(buffering=True)
                resp.read()
                status_codes = (resp.status, resp.reason, container_name)

                # Check that the status was a good one
                if resp.status == 404:
                    self.conn.request('PUT', path, headers=c_headers)

                    # Compatibility with Python 2.6
                    if sys.version_info < (2, 7, 0):
                        resp = self.conn.getresponse()
                    else:
                        resp = self.conn.getresponse(buffering=True)
                    resp.read()
                    status_codes = (resp.status, resp.reason, container_name)
                    if self.tur_arg['os_verbose']:
                        print('CREATING CONTAINER: %s %s %s' % status_codes)
                elif resp.status >= 300 or resp.status == None:
                    self.result_exception(resp=resp,
                                          headers=c_headers,
                                          authurl=self.url,
                                          jsonreq=path)
                    retry()
                else:
                    if self.tur_arg['os_verbose']:
                        print('Container Found %s %s %s' % status_codes)

                    # Put headers on the object if custom headers were specified
                    if self.tur_arg['object_headers']:
                        self.conn.request('POST', path, headers=c_headers)

                        # Compatibility with Python 2.6
                        if sys.version_info < (2, 7, 0):
                            resp = self.conn.getresponse()
                        else:
                            resp = self.conn.getresponse(buffering=True)

                        resp.read()
                        if resp.status >= 300:
                            self.result_exception(resp=resp,
                                                  headers=c_headers,
                                                  authurl=self.url,
                                                  jsonreq=path)
                            retry()
        except Exception, e:
            print 'ERROR\t: Shits broke son, here comes the stack trace:\t %s -> Exception\t: %s' % (sys.exc_info()[1], e)


    def put_uploader(self, file_path, file_name, container):
        """
        This is the simple upload Method. There is no file level checking at the target.
        The files are simply uploaded. 
        """
        try:
            for retry in generators.retryloop(attempts=self.tur_arg['error_retry'], delay=5, backoff=2):
                try:
                    # Set the headers if some custom ones were specified
                    f_headers = self.headers
                    if self.tur_arg['object_headers']:
                        f_headers.update(self.tur_arg['object_headers'])

                    # Get the path ready for action
                    r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                    filepath = quote(r_loc)

                    # Open our source file
                    with open(file_path, 'rb') as f:
                        self.conn.request('PUT', filepath, body=f, headers=f_headers)

                    # Compatibility with Python 2.6
                    if sys.version_info < (2, 7, 0):
                        resp = self.conn.getresponse()
                    else:
                        resp = self.conn.getresponse(buffering=True)

                    resp.read()

                    # Give us more data if we requested it
                    if self.tur_arg['os_verbose'] or self.tur_arg['debug']:
                        print 'INFO\t: %s %s %s' % (resp.status, resp.reason, file_name)
                        if self.tur_arg['debug']:
                            print 'MESSAGE\t: Upload path = %s ==> %s' % (file_path, filepath)
    
                    # Check that the status was a good one
                    if resp.status >= 300 or resp.status == None:
                        self.result_exception(resp=resp,
                                              headers=f_headers,
                                              authurl=self.url,
                                              jsonreq=filepath)
                        retry()

                except Exception, e:
                    print('Exception from within an upload Action : %s' % e)
        except IOError:
            print 'ERROR\t: path "%s" does not exist or is a broken symlink' % file_path
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % file_path
        except KeyboardInterrupt:
            pass


    def sync_uploader(self, file_path, file_name, container):
        """
        This is the Sync method which uploads files to the swift repository if they are not already found.
        If a file "name" is found locally and in the swift repository an MD5 comparison is done between the two files.
        If the MD5 is miss-matched the local file is uploaded to the repository. If custom meta data is specified,
        and the object exists the method will put the metadata onto the object.
        """
        #noinspection PyBroadException
        try:
            for retry in generators.retryloop(attempts=self.tur_arg['error_retry'], delay=5):
                # Set the headers if some custom ones were specified
                f_headers = self.headers
                if self.tur_arg['object_headers']:
                    f_headers.update(self.tur_arg['object_headers'])

                # Get the path ready for action
                r_loc = '%s/%s/%s' % (self.c_path, container, file_name)
                filepath = quote(r_loc)

                self.conn.request('HEAD', filepath, headers=f_headers)

                # Compatibility with Python 2.6
                if sys.version_info < (2, 7, 0):
                    resp = self.conn.getresponse()
                else:
                    resp = self.conn.getresponse(buffering=True)

                resp.read()                
    
                if resp.status == 404:
                    with open(file_path, 'rb') as f:
                        self.conn.request('PUT', filepath, body=f, headers=f_headers)

                    # Compatibility with Python 2.6
                    if sys.version_info < (2, 7, 0):
                        resp = self.conn.getresponse()
                    else:
                        resp = self.conn.getresponse(buffering=True)
                    resp.read()
    
                    if self.tur_arg['verbose']:
                        print 'INFO\t: %s %s %s' % (resp.status, resp.reason, file_name)
                elif resp.status >= 300 or resp.status == None:
                    self.result_exception(resp=resp,
                                          headers=f_headers,
                                          authurl=filepath,
                                          jsonreq=r_loc)
                    retry()
                else:
                    remotemd5sum = resp.getheader('etag')
                    md5 = hashlib.md5()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda : f.read(128 * md5.block_size), ''):
                            md5.update(chunk)
                    localmd5sum = md5.hexdigest()
    
                    if remotemd5sum != localmd5sum:
                        with open(file_path, 'rb') as f:
                            self.conn.request('PUT', filepath, body=f, headers=f_headers)

                        # Compatibility with Python 2.6
                        if sys.version_info < (2, 7, 0):
                            resp = self.conn.getresponse()
                        else:
                            resp = self.conn.getresponse(buffering=True)
                        resp.read()

                        if self.tur_arg['verbose']:
                            proc_dict = {'lmd5' : localmd5sum,
                                         'rmd5' : remotemd5sum,
                                         'rs' : resp.status,
                                         'rr' : resp.reason,
                                         'sjf' : file_name }
                            print('MESSAGE\t: CheckSumm Mis-Match %(lmd5)s != %(rmd5)s\n'
                                  '\t  File Upload : %(rs)s %(rr)s %(sjf)s' % proc_dict )
    
                        if resp.status >= 300:
                            self.result_exception(resp=resp,
                                                  headers=f_headers,
                                                  authurl=filepath,
                                                  jsonreq=r_loc)
                            retry()
                    else:
                        if self.tur_arg['verbose']:
                            print 'MESSAGE\t: CheckSum Match', localmd5sum

                        # Put headers on the object if custom headers were specified
                        if self.tur_arg['object_headers']:
                            self.conn.request('POST', filepath, headers=f_headers)

                            # Compatibility with Python 2.6
                            if sys.version_info < (2, 7, 0):
                                resp = self.conn.getresponse()
                            else:
                                resp = self.conn.getresponse(buffering=True)
                            resp.read()

                            if resp.status >= 300:
                                self.result_exception(resp=resp,
                                                      headers=self.headers,
                                                      authurl=filepath,
                                                      jsonreq=r_loc)
                                retry()
                                
        except IOError, e:
            if e.errno == errno.ENOENT:
                print 'ERROR\t: path "%s" does not exist or is a broken symlink' % filename
        except ValueError:
            print 'ERROR\t: The data for "%s" got all jacked up, so it got skipped' % filename
        except KeyboardInterrupt:
            pass
        except:
            print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]