# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def tsync_actions(subparser, source_args, container_args):
    """Tsync Arguments.

    :param source_args:
    :param shared_args:
    :param cdn_args:
    :param subparser:
    """

    tsync = subparser.add_parser(
        'tsync',
        parents=[source_args, container_args],
        help='Deprecated, Please use "upload --sync" instead'
    )
    tsync.set_defaults(tsync=True)
