# =============================================================================
# Copyright [2013] [kevin]
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
        parents=[container_args],
        help='List Objects in a container.'
    )
    list.set_defaults(list=True)

    # Provides for the stream Function.
    clone = subparser.add_parser(
        'clone',
        help='Clone Objects from one container to another.'
    )
    clone.set_defaults(clone=True)
    clone.add_argument('-sc',
                        '--source-container',
                        metavar='[CONTAINER]',
                        help='Target Container.',
                        required=True,
                        default=None)
    clone.add_argument('-tc',
                        '--target-container',
                        metavar='[CONTAINER]',
                        help='Target Container.',
                        required=True,
                        default=None)
    clone.add_argument('-tr',
                        '--target-region',
                        metavar='[REGION]',
                        help='Target Container.',
                        required=True,
                        default=None)
    clone.add_argument('--snet',
                        action='store_true',
                        help='Use Service Net to Stream the Objects.',
                        default=False)
