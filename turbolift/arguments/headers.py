# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
def header_args(parser):
    """Add in Optional Header Arguments."""

    headers = parser.add_argument_group('Header Options',
                                        'Headers are Parsed as KEY=VALUE'
                                        ' arguments. This is useful when'
                                        ' setting a custom header when'
                                        ' using a CDN URL or other HTTP'
                                        ' action which may rely on Headers.'
                                        ' Here are the default headers')
    headers.add_argument('-BH', '--base-headers',
                         metavar='[K=V]',
                         default=[],
                         action='append',
                         help=('These are the basic headers used for'
                               ' all Turbolift operations. Anything'
                               ' added here will modify ALL Turbolift'
                               ' Operations which leverage the API.'))
    headers.add_argument('-OH', '--object-headers',
                         metavar='[K=V]',
                         default=[],
                         action='append',
                         help=('These Headers only effect Objects'
                               ' (files).'))
    headers.add_argument('-CH', '--container-headers',
                         metavar='[K=V]',
                         default=[],
                         action='append',
                         help='These headers only effect Containers')
