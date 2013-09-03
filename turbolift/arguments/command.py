# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def command_actions(subparser, source_args, container_args, cdn_args):
    """Uploading Arguments.

    :param subparser:
    :param source_args:
    :param container_args:
    :param cdn_args:
    """

    # Provides for the list Function.
    list = subparser.add_parser(
        'list',
        help='List Objects in a container.'
    )
    list.set_defaults(list=True)

    list_group = list.add_mutually_exclusive_group()
    list_group.add_argument('-c',
                            '--container',
                            metavar='[CONTAINER]',
                            help='Target Container.',
                            default=None)
    list_group.add_argument('--all-containers',
                            action='store_true',
                            help='Target Container.',
                            default=None)