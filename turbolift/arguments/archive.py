# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def archive_actions(subparser, multi_source_args, container_args, regex):
    """Archive Arguments.

    :param subparser:
    :param multi_source_args:
    :param shared_args:
    :param cdn_args:
    """

    archaction = subparser.add_parser('archive',
                                      parents=[multi_source_args,
                                               container_args,
                                               regex],
                                      help=('Compress files or directories'
                                            ' into a single archive'))
    archaction.set_defaults(archive=True)
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
