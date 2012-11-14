#!/usr/bin/env python

# - title        : Upload for CloudFiles
# - description  : Want to upload a bunch files to cloudfiles? This will do it. 
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - usage        : python cfuploader.py
# - notes        : This is a CloudFiles Upload Script
# - Python       : >= 2.6

""" 
License Inforamtion

This software has no warranty, it is provided 'as is'. It is your responsibility
to validate the behavior of the routines and its accuracy using the code provided.
Consult the GNU General Public license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import argparse, sys, json, httplib, signal, os, multiprocessing, errno, hashlib, tarfile, datetime

from urllib import quote

version = '0.1'


"""This is the Matt Thode Authentication System, Modified by Me"""
def cfauth(user=None, apikey=None, region=None):
    """Set the Authentication URL"""
    if args.endpoint == 'LON':
        if args.url:
            print 'Using Override Auth URL to\t:', args.url
            authurl = args.url
        else:
            authurl = 'lon.identity.api.rackspacecloud.com'

    elif args.endpoint == 'DFW' or 'ORD':
        if args.url:
            print 'Using Override Auth URL to\t:', args.url
            authurl = args.url
        else:
            authurl = 'identity.api.rackspacecloud.com'

    if args.apikey:
        jsonreq = json.dumps({'auth': {'RAX-KSKEY:apiKeyCredentials': {'username': args.user, 'apiKey': args.apikey}}})
    elif args.password:
        jsonreq = json.dumps({'auth': {'passwordCredentials': {'username': args.user, 'password': args.password}}})
    else:
        print 'ERROR\t: This should have not happened.\nThere was no way to proceed, so I quit.'
        exit(1)

    if args.veryverbose:
        print 'JSON REQUEST: ' + jsonreq
    
    """make the request for authentication"""
    conn = httplib.HTTPSConnection(authurl, 443)
    if args.veryverbose:
        conn.set_debuglevel(1)
    headers = {'Content-type': 'application/json'}
    conn.request('POST', '/v2.0/tokens', jsonreq, headers)
    resp = conn.getresponse()
    readresp = resp.read()
    if resp.status >= 300:
        print '\n', 'REQUEST\t:', jsonreq, headers, authurl
        print '\n', 'ERROR\t:', resp.status, resp.reason, '\n'
        exit(1)
    json_response = json.loads(readresp)
    conn.close()

    if args.internal:
        print 'MESSAGE\t: Using the Service Network in the', args.endpoint, 'DC for', authurl

    """Process the Authentication Request"""
    if args.veryverbose:
        print '\nJSON decoded and pretty\n'
        print json.dumps(json_response, indent=2)
    cfdetails = {}
    try:
        catalogs = json_response['access']['serviceCatalog']
        for service in catalogs:
            if service['name'] == 'cloudFiles':
                for endpoint in service['endpoints']:
                    if endpoint['region'] == args.endpoint:
                        if args.internal:
                            cfdetails['endpoint'] = endpoint['internalURL']
                        else:
                            cfdetails['endpoint'] = endpoint['publicURL']
                        cfdetails['tenantid'] = endpoint['tenantId']
        cfdetails['token'] = json_response['access']['token']['id']
        if args.veryverbose:
            print 'Endpoint\t: ', cfdetails['endpoint']
            print 'Tenant\t\t: ', cfdetails['tenantid']
            print 'Token\t\t: ', cfdetails['token']
    except(KeyError, IndexError):
        print 'Error while getting answers from auth server.\nCheck the endpoint and auth credentials.'
    return cfdetails


def containercreate():
    global authdata
    try:
        """Create a Container if needed"""
        endpoint = authdata['endpoint'].split('/')[2]
        headers = {'X-Auth-Token': authdata['token']}
        filepath = '/v1/' + authdata['tenantid'] + '/' + quote(args.container)
        conn = httplib.HTTPSConnection(endpoint, 443)
        if args.veryverbose:
            conn.set_debuglevel(1)
        """Check to see if the Container is there"""
        conn.request('HEAD', filepath, headers=headers)
        resp = conn.getresponse()
        resp.read()
        """If Container is not found Create a Container"""
        if resp.status == 404:
            print '\n', 'MESSAGE\t:',resp.status, resp.reason, 'The Container', args.container, 'does not Exist'
            conn.request('PUT', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()
            if resp.status >= 300:
                print '\n', 'ERROR\t:',resp.status, resp.reason, args.container, '\n'
                exit(1)
            print '\n', 'CREATING CONTAINER\t:', args.container, '\n', 'CONTAINER STATUS\t:', resp.status, resp.reason, '\n'
        conn.close()
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
        raise


def get_filenames():
    if args.upload or args.tsync:
        directorypath = args.upload or args.tsync
        if os.path.isdir(directorypath) == True:
            rootdir = os.path.normpath(directorypath) + os.sep
            target = os.path.realpath(rootdir)
            """Get all of the files as they are found in the directory specified"""
            fileList = []
            if args.veryverbose:
                print rootdir
            # Locate all of the files found in the given directory
            for root, subFolders, files in os.walk(rootdir):
                for file in files:
                    fileList.append(os.path.join(root,file))
            if args.veryverbose:
                print fileList
            print 'MESSAGE\t: In', '"'+target+'"', len(fileList), 'files have been found.\n'
        else:
            print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
            print 'MESSAGE\t: Try Again but this time with a valid directory path'
            exit(1)

    if args.file:
        directorypath = args.file
        if os.path.isfile(directorypath) == True:
            fileList = []
            fileList.append(os.path.realpath(directorypath))
            if args.veryverbose:
                print 'file name', fileList
        else:
            print 'ERROR\t: file %s does not exist, or is a broken symlink' % directorypath
            print 'MESSAGE\t: Try Again but this time with a valid file path'
            exit(1)

    if args.compress:
        format = "%a%b%d-%H.%M.%S.%Y."
        today = datetime.datetime.today()
        ts = today.strftime(format)

        tarList = []
        print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
        global archivename
        archivename = ts + args.container + '.tgz'
        # create a tar archive
        tar = tarfile.open(archivename,'w:gz')
        for name in fileList:
            tarname = os.path.realpath(name)
            tar.add(tarname)
        tar.close()
        tarList.append(os.path.realpath(archivename))
        if args.veryverbose:
            print tarList
        return tarList
    else:
        return fileList

def cfrsync(filename=None):
    global authdata
    """Put all of the files that were found into the container"""
    f = open(filename)
    if args.veryverbose:
        print f
    try:
        """Put all of the files that were found into the container"""
        rootdir = os.path.normpath(args.tsync) + os.sep
        justfilename = filename.split(rootdir)[1]
        
        if args.veryverbose:
            print justfilename
        
        retry = True
        while retry:
            retry = False
            """Upload All files found in the spcified cfrsync to a given container"""
            endpoint = authdata['endpoint'].split('/')[2]
            headers = {'X-Auth-Token': authdata['token']}
            filepath = '/v1/' + authdata['tenantid'] + '/' + quote(args.container + '/' + justfilename)
            
            conn = httplib.HTTPSConnection(endpoint, 443)
            
            if args.veryverbose:
                conn.set_debuglevel(1)
            
            """Check to see if the Container is there"""
            conn.request('HEAD', filepath, headers=headers)
            resp = conn.getresponse()
            resp.read()
            conn.close()
            
            if resp.status == 404:
                f = open(filename)
                if args.veryverbose:
                    print f
                if args.veryverbose:
                    conn.set_debuglevel(1)
                """Put all of the files that were found into the container"""
                conn.request('PUT', filepath, body=f, headers=headers)
                f.close()
                resp = conn.getresponse()
                resp.read()
                conn.close()
                if args.progress:
                    print resp.status, resp.reason, justfilename
            else:
                md5 = hashlib.md5()
                with open(filename, 'rb') as f:
                    for chunk in iter(lambda: f.read(128*md5.block_size), b''):
                        md5.update(chunk)
                f.close()
                localmd5sum = md5.hexdigest()
                remotemd5sum = resp.getheader('etag')
                
                if remotemd5sum != localmd5sum:
                    if args.veryverbose:
                        conn.set_debuglevel(1)
                    fupdate = open(filename)
                    if args.veryverbose:
                        print f
                    conn.request('PUT', filepath, body=fupdate, headers=headers)
                    conn.close()
                    fupdate.close()
                    if args.progress:
                        print 'MESSAGE\t: CheckSumm Mis-Match', localmd5sum, '!=', remotemd5sum, '\n\t ', 'File Upload :', resp.status, resp.reason, justfilename
                else:
                    if args.progress:
                        print 'MESSAGE\t: CheckSumm Match', localmd5sum
            
            """Reauthenticate if 401"""
            if resp.status == 401:
                print 'MESSAGE\t: Token Seems to have expired, Forced Reauthentication is happening.'
                authdata = cfauth()
                retry = True
                continue
            
            """Highlight any errors that happen on Upload"""
            if resp.status >= 300:
                print 'ERROR\t:',resp.status, resp.reason, justfilename, '\n', f, '\n'
            conn.close()
    
    except IOError, e:
        if e.errno == errno.ENOENT:
            print 'ERROR\t: path %s does not exist or is a broken symlink' % justfilename
    except ValueError:
        print 'ERROR\t: The data for %s got all jacked up, so it got skiped' % justfilename
    except KeyboardInterrupt, e:
        pass
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
        raise


def uploader(filename=None):
    global authdata
    f = open(filename)
    if args.veryverbose:
        print f
    try:
        """Put all of the files that were found into the container"""
        if args.compress or args.file:
            justfilename = filename.split(os.path.dirname(filename) + os.sep)[1]
        else:
            rootdir = os.path.normpath(args.upload) + os.sep
            justfilename = filename.split(rootdir)[1]
        
        retry = True
        while retry:
            retry = False
            """Upload All files found in the spcified directory to a given container"""
            endpoint = authdata['endpoint'].split('/')[2]
            headers = {'X-Auth-Token': authdata['token']}
            filepath = '/v1/' + authdata['tenantid'] + '/' + quote(args.container + '/' + justfilename)
            
            conn = httplib.HTTPSConnection(endpoint, 443)
            
            if args.veryverbose:
                conn.set_debuglevel(1)
            
            """Put all of the files that were found into the container"""
            conn.request('PUT', filepath, body=f, headers=headers)
            f.close()
            resp = conn.getresponse()
            resp.read()
            if args.progress:
                print resp.status, resp.reason, justfilename
            
            """Reauthenticate if 401"""
            if resp.status == 401:
                print 'MESSAGE\t: Token Seems to have expired, Forced Reauthentication is happening.'
                authdata = cfauth()
                retry = True
                continue
            
            """Highlight any errors that happen on Upload"""
            if resp.status >= 300:
                print 'ERROR\t:',resp.status, resp.reason, justfilename, '\n', f, '\n'

            conn.close()
    
    except IOError, e:
        if e.errno == errno.ENOENT:
            print 'ERROR\t: path %s does not exist or is a broken symlink' % justfilename
    except ValueError:
        print 'ERROR\t: The data for %s got all jacked up, so it got skiped' % justfilename
    except KeyboardInterrupt, e:
        pass
    except:
        print 'ERROR\t: Shits broke son, here comes the stack trace:\n', sys.exc_info()[1]
        raise

def init_worker():
    """Watch for signals"""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_turbolift():
    global authdata
    global args
    """Look for flags"""
    defaultcc = 10
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50), usage='%(prog)s [-u] [-a | -p] [options]', description='Uploads lots of Files Quickly, Using the unpatented GPLv3 Cloud Files %(prog)s')
    
    parser.add_argument('-u', '--user', nargs='?', help='Defaults to env[OS_USERNAME]', default=os.environ.get('OS_USERNAME', None))
    
    agroup = parser.add_mutually_exclusive_group()
    agroup.add_argument('-a', '--apikey', nargs='?', help='Defaults to env[OS_API_KEY]', default=os.environ.get('OS_API_KEY', None))
    agroup.add_argument('-p', '--password', nargs='?', help='Defaults to env[OS_PASSWORD]', default=os.environ.get('OS_PASSWORD', None))
    
    parser.add_argument('-e', '--endpoint', choices=['dfw', 'lon', 'ord'], required=True, help='Rackspace Specific Datacenter')
    parser.add_argument('-c', '--container', nargs='?', required=True, help='Specifies the Container')

    bgroup = parser.add_mutually_exclusive_group(required=True)
    bgroup.add_argument('-U', '--upload', nargs='?', help='A local Directory to Upload')
    bgroup.add_argument('-F', '--file', nargs='?', help='A local File to Upload')
    bgroup.add_argument('-T', '--tsync', nargs='?', help='Sync a local Directory to Cloud Files. Similar to RSYNC')

    """Optional Arguments"""
    parser.add_argument('-I', '--internal', action='store_true', help='Use Service Network')
    parser.add_argument('-P', '--progress', action='store_true', help='Shows Progress While Uploading')
    parser.add_argument('-V', '--veryverbose', action='store_true', help='Turn up verbosity to over 9000')
    
    cgroup = parser.add_mutually_exclusive_group()
    cgroup.add_argument('--compress', action='store_true', help='Compress a file or directory into a single archive')
    cgroup.add_argument('--cc', nargs='?', help='Container Upload Concurrency', type=int, default=defaultcc)
    
    parser.add_argument('--url', nargs='?', help='Defaults to env[OS_AUTH_URL]', default=os.environ.get('OS_AUTH_URL', None))
    parser.add_argument('--version', action='version', version=version)

    args = parser.parse_args()
    args.endpoint = args.endpoint.upper()

    if not args.user:
        print '\nNo Username was provided\n'
        parser.print_help()
        exit(1)

    if not (args.apikey or args.password):
        print '\nNo API Key or Password was provided\n'
        parser.print_help()
        exit(1)

    if args.tsync:
        if args.compress:
            print 'ERROR\t: You can not use compression with this function.', '\n', 'MESSAGE\t: I have quit the application, please try again.'
            exit(1)

    if args.veryverbose:
        args.progress = True

    try:
        authdata = cfauth()
        containercreate()
        """Start Uploading"""
        print 'Beginning the Upload Process'
        """Uploads the contents of a directory"""
        if (args.upload or args.tsync or args.file):
            """From the amount of CORES create the max processes"""
            if args.cc:
                if args.cc > 150:
                    print '\nMESSAGE\t: You have set the Concurency Override to', args.cc, '\n\t  This is a lot of Processes and could fork bomb your\n\t  system or cause other nastyness.'
                    raw_input("\t  You have been warned, Press Enter to Continue\n")
                
                if not args.cc == defaultcc:
                    print 'MESSAGE\t: Setting a Concurency Override of', args.cc
            
            if args.compress:
                multipools = 1
            else:
                multipools = args.cc
            
            pool = multiprocessing.Pool(multipools, init_worker)
            
            if (args.veryverbose or args.progress):
                print '\nWe are going to create Processes :', multipools, '\n'
            
            if args.upload or args.file:
                p = pool.map(uploader, get_filenames())
            
            if args.tsync:
                p = pool.map(cfrsync, get_filenames())
            
            pool.close()
            pool.join()
            
            if args.compress:
                os.remove(archivename)
        
        if not (args.upload or args.file or args.tsync):
            print 'ERROR\t: Somehow I continuted but I dont know how to proceed. So I Quit.'
            print 'MESSAGE\t: here comes the stack trace:\n', sys.exc_info()[1]
            exit(1)
        
        print "Operation Completed, Quitting normallyy"
        exit(0)
    
    except KeyboardInterrupt:
        print "\nCaught KeyboardInterrupt, terminating workers\n"
        pool.terminate()
        if args.compress:
            os.remove(archivename)
        exit(1)