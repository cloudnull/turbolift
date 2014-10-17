# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os

from turbolift import info


def auth_group(parser):
    """Base Authentication Argument Set."""

    authgroup = parser.add_argument_group('Authentication',
                                          'Authentication against'
                                          ' the OpenStack API')

    a_keytype = authgroup.add_mutually_exclusive_group()
    a_keytype.add_argument('-a',
                           '--os-apikey',
                           metavar='[API_KEY]',
                           help='Defaults to env[OS_API_KEY]',
                           default=os.environ.get('OS_API_KEY', None))
    a_keytype.add_argument('-p',
                           '--os-password',
                           metavar='[PASSWORD]',
                           help='Defaults to env[OS_PASSWORD]',
                           default=os.environ.get('OS_PASSWORD', None))

    a_usertype = authgroup.add_mutually_exclusive_group()
    a_usertype.add_argument('-u',
                            '--os-user',
                            metavar='[USERNAME]',
                            help='Defaults to env[OS_USERNAME]',
                            default=os.environ.get('OS_USERNAME', None))
    authgroup.add_argument('--os-tenant',
                           metavar='[TENANT]',
                           help='Defaults to env[OS_TENANT_NAME]',
                           default=os.environ.get('OS_TENANT_NAME', None))
    authgroup.add_argument('--os-token',
                           metavar='[TOKEN]',
                           help='Defaults to env[OS_TOKEN]',
                           default=os.environ.get('OS_TOKEN', None))

    a_regiontype = authgroup.add_mutually_exclusive_group()
    a_regiontype.add_argument('-r',
                              '--os-region',
                              metavar='[REGION]',
                              help='Defaults to env[OS_REGION_NAME]',
                              default=os.environ.get('OS_REGION_NAME', None))
    a_regiontype.add_argument('--os-rax-auth',
                              choices=info.__rax_regions__,
                              help=('Authentication Plugin for Rackspace Cloud'
                                    ' env[OS_RAX_AUTH]'),
                              default=os.getenv('OS_RAX_AUTH', None))
    a_regiontype.add_argument('--os-hp-auth',
                              choices=info.__hpc_regions__,
                              help=('Authentication Plugin for HP Cloud'
                                    ' env[OS_HP_AUTH]'),
                              default=os.getenv('OS_HP_AUTH', None))

    a_authurl = authgroup.add_mutually_exclusive_group()
    a_authurl.add_argument('--os-auth-url',
                           metavar='[AUTH_URL]',
                           help='Defaults to env[OS_AUTH_URL]',
                           default=os.environ.get('OS_AUTH_URL', None))
    authgroup.add_argument('--os-version',
                           metavar='[VERSION_NUM]',
                           default=os.getenv('OS_VERSION', 'v2.0'),
                           help='env[OS_VERSION]')

    # v1 auth
    a_keytype.add_argument('--st-key',
                           metavar='[API_KEY]',
                           help='v1 Auth API Key. Defaults to env[ST_KEY]',
                           default=os.environ.get('ST_KEY', None))
    a_usertype.add_argument('--st-user',
                            metavar='[USERNAME]',
                            help='v1 Auth Username. Defaults to env[ST_USER]',
                            default=os.environ.get('ST_USER', None))
    a_authurl.add_argument('--st-auth',
                           metavar='[AUTH_URL]',
                           help='v1 Auth URL. Defaults to env[ST_AUTH]',
                           default=os.environ.get('ST_AUTH', None))
