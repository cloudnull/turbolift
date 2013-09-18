# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def download_actions(subparser, source_args, container_args, time_args):
    """Download Actions.

    :param subparser:
    :param source_args:
    :param shared_args:
    """

    download = subparser.add_parser('download',
                                    parents=[source_args,
                                             container_args,
                                             time_args],
                                    help=('Downloads everything from a'
                                          ' given container creating a'
                                          ' target Directory if it does'
                                          ' not exist'))
    download.set_defaults(download=True)
    download.add_argument('--sync',
                          action='store_true',
                          help=('Looks at local file vs Remote File and if a'
                                ' difference is detected the file is'
                                ' uploaded.'),
                          default=None)
    download.add_argument('--restore-perms',
                          action='store_true',
                          help=('If The object has permissions saved as'
                                ' metadata restore those permissions on the'
                                ' local object'),
                          default=None)
    dwfilter = download.add_mutually_exclusive_group()
    dwfilter.add_argument('-o',
                          '--object',
                          metavar='[NAME]',
                          default=[],
                          action='append',
                          help=('Name of a specific Object that you want'
                                ' to Download.'))
    dwfilter.add_argument('-d',
                          '--dir',
                          metavar='[NAME]',
                          default=[],
                          action='append',
                          help=('Name of a directory path that you want'
                                ' to Download.'))
