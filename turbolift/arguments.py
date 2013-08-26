# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import argparse
import os
import sys

from turbolift import info


def get_values():
    """Look for flags, these are all of the available options for Turbolift."""

    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=50),
        usage='%(prog)s',
        description=('Uploads lots of Files Quickly Cloud Files %(prog)s'),
        epilog=info.VINFO)

    # Setup for the positional Arguments
    subparser = parser.add_subparsers(title='Infrastructure Spawner',
                                      metavar='<Commands>\n')
    authgroup = parser.add_argument_group('Authentication',
                                          'Authentication against'
                                          ' the OpenStack API')
    optionals = parser.add_argument_group('Additional Options',
                                          'Things you might want to'
                                          ' add to your operation')
    headers = parser.add_argument_group('Optional Header Options',
                                        'Headers are Parsed as KEY=VALUE'
                                        ' arguments. This is useful when'
                                        ' setting a custom header when'
                                        ' using a CDN URL or other HTTP'
                                        ' action which may rely on Headers.'
                                        ' Here are the default headers')

    # Adds a parent set of arguments that are shared between most functions
    cdn_args = argparse.ArgumentParser(add_help=False)
    cdn_args.add_argument('--cdn-enabled',
                          action='store_true',
                          default=None,
                          help='Enable the CDN for a Container')
    cdn_args.add_argument('--cdn-ttl',
                          metavar='[TTL]',
                          type=int,
                          default=259200,
                          help='Set the TTL on a CDN Enabled Container.')
    cdn_args.add_argument('--cdn-logs',
                          action='store_true',
                          default=False,
                          help='Set CDN Logging on a Container')

    del_args = argparse.ArgumentParser(add_help=False)
    del_args.add_argument('--save-container',
                          action='store_true',
                          default=None,
                          help=('This will allow the container to remain'
                                ' untouched and intact, but only the'
                                ' container.'))

    shared_args = argparse.ArgumentParser(add_help=False)
    shared_args.add_argument('-c', '--container',
                             metavar='<name>',
                             required=True,
                             help='Specifies the Container')

    source_args = argparse.ArgumentParser(add_help=False)
    source_args.add_argument('-s',
                             '--source',
                             metavar='<local>',
                             required=True,
                             help='Local content to be uploaded')

    multi_source_args = argparse.ArgumentParser(add_help=False)
    multi_source_args.add_argument('-s', '--source',
                                   metavar='<locals>',
                                   default=[],
                                   action='append',
                                   required=True,
                                   help=('Local content to be uploaded,'
                                         ' this can be specified as many'
                                         ' times as need be. The "Source"'
                                         ' can be a directory Path or'
                                         ' File'))

    # All of the positional Arguments
    upaction = subparser.add_parser('upload',
                                    parents=[source_args,
                                             shared_args,
                                             cdn_args],
                                    help=('Upload Action, Type of upload to'
                                          ' be performed as well as'
                                          ' Source and Destination'))
    upaction.set_defaults(upload=True)

    taction = subparser.add_parser('tsync',
                                   parents=[source_args,
                                            shared_args,
                                            cdn_args],
                                   help=('T-Sync Action, Type of upload to'
                                         ' be performed as well as'
                                         ' Source and Destination'))
    taction.set_defaults(tsync=True)

    archaction = subparser.add_parser('archive',
                                      parents=[multi_source_args,
                                               shared_args,
                                               cdn_args],
                                      help=('Compress files or directories'
                                            ' into a single archive'))
    archaction.set_defaults(archive=True)

    cpdaction = subparser.add_parser('con-per-dir',
                                     parents=[multi_source_args, cdn_args],
                                     help=('Uploads everything from a'
                                           ' given source creating a single'
                                           ' Container per Directory'))
    cpdaction.set_defaults(con_per_dir=True)

    dwnaction = subparser.add_parser('download',
                                     parents=[source_args, shared_args],
                                     help=('Downloads everything from a'
                                           ' given container creating a'
                                           ' target Directory if it does'
                                           ' not exist'))
    dwnaction.add_argument('--dl-sync',
                           action='store_true',
                           help=('Looks at local file and if a difference is'
                                 ' detected the file is downloaded.'),
                           default=False)
    dwnaction.set_defaults(download=True)

    delaction = subparser.add_parser('delete',
                                     parents=[del_args, shared_args],
                                     help=('Deletes everything in a given'
                                           ' container Including the'
                                           ' container.'))
    delaction.set_defaults(delete=True)

    # Base Authentication Argument Set
    authgroup.add_argument('-u',
                           '--os-user',
                           metavar='[USERNAME]',
                           help='Defaults to env[OS_USERNAME]',
                           default=os.environ.get('OS_USERNAME', None))
    authgroup.add_argument('-a',
                           '--os-apikey',
                           metavar='[API_KEY]',
                           help='Defaults to env[OS_API_KEY]',
                           default=os.environ.get('OS_API_KEY', None))
    authgroup.add_argument('-p',
                           '--os-password',
                           metavar='[PASSWORD]',
                           help='Defaults to env[OS_PASSWORD]',
                           default=os.environ.get('OS_PASSWORD', None))
    authgroup.add_argument('-r',
                           '--os-region',
                           metavar='[REGION]',
                           help='Defaults to env[OS_REGION_NAME]',
                           default=os.environ.get('OS_REGION_NAME', None))
    authgroup.add_argument('--os-auth-url',
                           metavar='[AUTH_URL]',
                           help='Defaults to env[OS_AUTH_URL]',
                           default=os.environ.get('OS_AUTH_URL', None))
    authgroup.add_argument('--os-rax-auth',
                           choices=['dfw', 'ord', 'lon', 'syd'],
                           help='Rackspace Cloud Authentication',
                           default=None)
    authgroup.add_argument('--os-version',
                           metavar='[VERSION_NUM]',
                           default=os.getenv('OS_VERSION', 'v2.0'),
                           help='env[OS_VERSION]')
    authgroup.add_argument('--os-swift-version',
                           metavar='[OS_SWIFT_VERSION]',
                           default=os.getenv('OS_SWIFT_VERSION', 'v1'),
                           help='env[OS_VERSION]')
    authgroup.add_argument('--use-http',
                           action='store_true',
                           default=None,
                           help=('Forces the NOVA API to Use HTTP'
                                 ' instead of HTTPS'))
    authgroup.add_argument('--os-verbose',
                           action='store_true',
                           default=None,
                           help=('Make the OpenStack Authentication'
                                 ' Verbose'))

    # Archive Arguments
    archaction.add_argument('--tar-name',
                            metavar='<name>',
                            help='Name To Use for the Archive')
    archaction.add_argument('--no-cleanup',
                            action='store_true',
                            help=('Used to keep the compressed Archive.'
                                  ' The archive will be left in the Users'
                                  ' Home Folder'))
    archaction.add_argument('--verify',
                            action='store_true',
                            help=('Will open a created archive and verify'
                                  ' its contents. Used when needing to know'
                                  ' without a doubt that all the files that'
                                  ' were specified were compressed.'))

    # Optional Aguments
    optionals.add_argument('-P',
                           '--preserve-path',
                           action='store_true',
                           help=('This will preserve the full path to a file'
                                 ' when uploaded to a container.'))
    optionals.add_argument('-I',
                           '--internal',
                           action='store_true',
                           help='Use Service Network')
    optionals.add_argument('--error-retry',
                           metavar='[ATTEMPTS]',
                           type=int,
                           default=5,
                           help=('This option sets the number of attempts'
                                 ' %(prog)s will attempt an operation'
                                 ' before quiting. The default is 5. This'
                                 ' is useful if you have a spotty'
                                 ' network or ISP.'))
    optionals.add_argument('--cc',
                           metavar='[CONCURRENCY]',
                           type=int,
                           default=50,
                           help='Upload Concurrency')
    optionals.add_argument('--no-sort',
                           action='store_true',
                           default=False,
                           help=('By default when getting the list of files'
                                 ' to upload Turbolift will sort the files'
                                 ' by size. If you have a lot of files this'
                                 ' may be a time consuming operation.'
                                 ' This flag will disable that function.'))
    optionals.add_argument('--system-config',
                           metavar='[CONFIG-FILE]',
                           type=str,
                           default=None,
                           help=('Path to your Configuration file. This is'
                                 ' an optional argument used to spec '
                                 ' credentials.'))
    optionals.add_argument('--quiet',
                           action='store_true',
                           help='Make %(prog)s Shut the hell up')
    optionals.add_argument('--verbose',
                           action='store_true',
                           help='Be verbose While Uploading')
    optionals.add_argument('--debug',
                           action='store_true',
                           help='Turn up verbosity to over 9000')
    optionals.add_argument('--version',
                           action='version',
                           version=info.__VN__)

    # Optional Headers
    headers.add_argument('--base-headers',
                         metavar='[KEY=VALUE]',
                         default=[],
                         action='append',
                         help=('These are the basic headers used for'
                               ' all Turbolift operations. Anything'
                               ' added here will modify ALL Turbolift'
                               ' Operations which leverage the API.'))
    headers.add_argument('--object-headers',
                         metavar='[KEY=VALUE]',
                         default=[],
                         action='append',
                         help=('These Headers only effect Objects'
                               ' (files).'))
    headers.add_argument('--container-headers',
                         metavar='[KEY=VALUE]',
                         default=[],
                         action='append',
                         help='These headers only effect Containers')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit('Give me something to do and I will do it')

    # Parse the arguments
    args = parser.parse_args()
    set_args = vars(args)

    # Parse Config File
    if set_args.get('system_config'):
        from turbolift.operations import systemconfig
        set_args = (
            systemconfig.ConfigurationSetup(set_args).config_args())

    # Interperate the Parsed Arguments
    set_args['defaultcc'] = set_args['cc']

    default_h = {'Connection': 'Keep-alive',
                 'X-Auth-Token': None}

    if set_args.get('base_headers'):
        added_h = dict(kv.split('=') for kv in set_args['base_headers'])
        default_h.update(added_h)
        set_args['base_headers'] = default_h
    else:
        set_args['base_headers'] = default_h

    if set_args.get('object_headers'):
        _oh = [kv.split('=') for kv in set_args['object_headers']]
        set_args['object_headers'] = dict(_oh)

    if set_args.get('container_headers'):
        _ch = [kv.split('=') for kv in set_args['container_headers']]
        set_args['container_headers'] = dict(_ch)

    if set_args.get('os_region'):
        set_args['os_region'] = set_args['os_region'].upper()

    if set_args.get('os_rax_auth'):
        set_args['os_rax_auth'] = set_args['os_rax_auth'].upper()

    if not set_args.get('os_user'):
        parser.print_help()
        sys.exit('\nNo Username was provided, use [--os-user]\n')

    if not any([set_args.get('os_apikey'), set_args.get('os_password')]):
        parser.print_help()
        sys.exit('No API Key or Password was provided, use [--os-apikey]')

    if set_args.get('os_apikey'):
        set_args['os_password'] = set_args['os_apikey']

    if set_args.get('os_rax_auth') and set_args.get('os_region'):
        parser.print_help()
        sys.exit('You can\'t use both [--os-rax-auth] and [--os-region] in'
                 ' the same command, so I quit...')

    if set_args.get('archive'):
        set_args['cc'] = 1
        print('MESSAGE\t: Because I have not figured out how to'
              ' multi-thread Archiving, the max Concurrency is 1')
    elif set_args.get('cc', 0) > 150:
        try:
            print('MESSAGE\t: You have set the Concurrency Override to "%s"\n'
                  '\t  This is a lot of Processes and could fork bomb your\n'
                  '\t  system or cause other nastiness.\n' % set_args['cc'])
            raw_input('\t  You have been warned, Press Enter to Continue\n')
        except Exception:
            sys.exit('Shutting Down...')
    elif set_args.get('cc', 0) != set_args.get('defaultcc', 0):
        print('MESSAGE\t: Setting a Concurrency Override of',
              set_args.get('cc'))

    if set_args.get('debug'):
        set_args['os_verbose'] = True
        set_args['verbose'] = True
        print('BASIC HEADERS : "%s"\n'
              'DEFAULT ARGUMENTS : %s\n' % (default_h, set_args))
    return set_args
