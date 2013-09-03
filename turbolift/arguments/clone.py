# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def clone_actions(subparser):
    """Uploading Arguments.

    :param subparser:
    """

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
    clone.add_argument('--target-snet',
                       action='store_true',
                       help='Use Service Net to Stream the Objects.',
                       default=False)
    clone.add_argument('--clone-headers',
                       action='store_true',
                       help=('Query the source object for headers and restore'
                             ' them on the target.'),
                       default=False)
