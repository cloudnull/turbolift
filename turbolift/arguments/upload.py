# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def upload_actions(subparser, source_args, container_args, time_args, regex):
    """Uploading Arguments.

    :param subparser:
    :param source_args:
    :param shared_args:
    :param cdn_args:
    """

    upload = subparser.add_parser(
        'upload',
        parents=[source_args, container_args, time_args, regex],
        help='Upload files to SWIFT, -CloudFiles-'
    )
    upload.set_defaults(upload=True)
    upload.add_argument('--sync',
                        action='store_true',
                        help=('Looks at local file vs Remote File and if a '
                              'difference is detected the file is uploaded.'),
                        default=False)
    upload.add_argument('--delete-remote',
                        action='store_true',
                        help=('Compare the REMOTE container and LOCAL file'
                              ' system and if the REMOTE container has objects'
                              ' NOT found in the LOCAL File System, DELETE THE'
                              ' REMOTE OBJECTS.'),
                        default=False)
    upload.add_argument('--save-perms',
                        action='store_true',
                        help=('Save the UID, GID, and MODE, of a file as meta'
                              ' data on the object.'),
                        default=False)
