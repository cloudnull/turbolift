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
import sys

from turbolift import info
from turbolift import utils
from turbolift.arguments import archive
from turbolift.arguments import authgroup
from turbolift.arguments import conperdir
from turbolift.arguments import delete
from turbolift.arguments import download
from turbolift.arguments import headers
from turbolift.arguments import optionals
from turbolift.arguments import tsync
from turbolift.arguments import upload


def setup_parser():
    """Look for flags, these are all of the available options for Turbolift.

    :returns parser, subparser:
    """

    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=50
        ),
        usage='%(prog)s',
        description='Uploads lots of Files Quickly Cloud Files %(prog)s',
        epilog=info.VINFO)

    # Setup for the positional Arguments
    subparser = parser.add_subparsers(title='SWIFT -CloudFiles- Uploader',
                                      metavar='<Commands>\n')

    return parser, subparser


def shared_args():
    """Create parent Arguments.

    :param argp:
    :returns cdn_args, del_args, container_args, source_args, msource_args:
    """

    # CDN Arguments
    cdn_args = argparse.ArgumentParser(add_help=False)
    cdn_args.add_argument('--cdn-toggle',
                          choices=[True, False],
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

    # Delete Arguments
    del_args = argparse.ArgumentParser(add_help=False)
    del_args.add_argument('--save-container',
                          action='store_true',
                          default=None,
                          help=('This will allow the container to remain'
                                ' untouched and intact, but only the'
                                ' container.'))

    # Container Arguments
    container_args = argparse.ArgumentParser(add_help=False)
    container_args.add_argument('-c', '--container',
                                metavar='<name>',
                                required=True,
                                help='Specifies the Container')

    # Local Source Arguments
    source_args = argparse.ArgumentParser(add_help=False)
    source_args.add_argument('-s',
                             '--source',
                             metavar='<local>',
                             required=True,
                             help='Local content to be uploaded')

    # Local Multi-Source Arguments
    msource_args = argparse.ArgumentParser(add_help=False)
    msource_args.add_argument('-s', '--source',
                              metavar='<locals>',
                              default=[],
                              action='append',
                              required=True,
                              help=('Local content to be uploaded, this can be'
                                    ' specified as many times as need be. The'
                                    ' "Source" can be a directory Path or'
                                    ' File'))

    return cdn_args, del_args, container_args, source_args, msource_args


def default_args(parser):
    """Add in Default Arguments to the parser.

    :param parser:
    """

    parser.add_argument('--log-level',
                        choices=['warn', 'info', 'error', 'critical', 'debug'],
                        default='info',
                        help='Set the Log Level')
    parser.add_argument('--version',
                        '-V',
                        action='version',
                        version=info.VINFO)


def args_setup():
    """Set and return all Parsed all Arguments.

    :return parser:
    """

    parser, subparser = setup_parser()

    default_args(parser=parser)

    # Shared Arguments
    cdn, remove, container, source, msource = shared_args()

    # Optional Arguments
    authgroup.auth_group(parser=parser)
    headers.header_args(parser=parser)
    optionals.optional_args(parser=parser)

    # Subparser Positional Arguments
    archive.archive_actions(subparser=subparser,
                            multi_source_args=msource,
                            container_args=container,
                            cdn_args=cdn)
    delete.delete_actions(subparser=subparser,
                          del_args=remove,
                          container_args=container)
    download.download_actions(subparser=subparser,
                              source_args=source,
                              container_args=container)
    tsync.tsync_actions(subparser=subparser,
                        source_args=source,
                        container_args=container,
                        cdn_args=cdn)
    upload.upload_actions(subparser=subparser,
                          source_args=source,
                          container_args=container,
                          cdn_args=cdn)
    return parser


def get_help():
    """Get Argument help.

    :returns parser.print_help(): returns help information.
    """

    parser = args_setup()
    return parser.print_help()


def get_args():
    """Parse all arguments to run the application.

    :returns vars(parser.parse_args()): args as a dictionary
    """

    parser = args_setup()
    args = vars(parser.parse_args())
    return understand_args(set_args=args)


def understand_args(set_args):
    """parse the arguments.

    :param parser:
    :return args:
    """

    def configurator():
        """Returns Arguments from a configuration file.

        :return set_args:
        """

        from turbolift.operations import systemconfig
        return systemconfig.ConfigurationSetup(args=set_args).config_args()

    def set_header_args():
        """return base Headers.

        :return set_args:
        """

        for htp in ['object_headers', 'container_headers', 'base_headers']:
            set_args[htp] = utils.keys2dict(
                chl=set_args.get(htp)
            )

    # Parse Config File
    if set_args.get('system_config'):
        set_args = configurator()

    # Return all types of headers
    set_header_args()

    if set_args.get('os_region') is not None:
        set_args['os_region'] = set_args['os_region'].upper()

    if set_args.get('os_rax_auth') is not None:
        set_args['os_rax_auth'] = set_args['os_rax_auth'].upper()

    if set_args.get('os_user') is None:
        sys.exit('\nNo Username was provided, use [--os-user]\n')

    if not any([set_args.get('os_apikey'), set_args.get('os_password')]):
        sys.exit('No APIKey or Password was provided, use [--os-apikey]'
                 ' or [--os-password]')

    if set_args.get('archive') is True:
        set_args['cc'] = 1

    if set_args.get('tsync'):
        import time
        import warnings
        set_args['upload'] = True
        set_args['sync'] = True
        set_args['tsync'] = None
        warnings.simplefilter("always")
        msg = ('The "tsync" method has been replaced by "upload --sync"'
               ' Please check "upload --help" for more information.')
        warnings.warn(msg, PendingDeprecationWarning)
        time.sleep(1)

    if set_args.get('debug') is True:
        set_args['verbose'] = True
        set_args['log_level'] = 'debug'
        print('DEFAULT ARGUMENTS : %s\n' % set_args)

    # Parse and return the arguments
    return utils.dict_pop_none(dictionary=set_args)
