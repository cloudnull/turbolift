# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def command_actions(subparser, source_args, container_args, cdn_args,
                    time_args, regex):
    """Uploading Arguments.

    :param subparser:
    :param source_args:
    :param container_args:
    :param cdn_args:
    """

    # Provides for the show Function.
    show = subparser.add_parser(
        'show',
        parents=[container_args],
        help='List Objects in a container.'
    )
    show.set_defaults(show=True)
    show_group = show.add_mutually_exclusive_group()
    show_group.add_argument('-o',
                            '--object',
                            metavar='[NAME]',
                            help='Target Object.',
                            default=None)
    show_group.add_argument('--cdn-info',
                            action='store_true',
                            help='Show Info on the Container for CDN',
                            default=None)

    # Provides for the list Function.
    lister = subparser.add_parser(
        'list',
        parents=[time_args, regex],
        help='List Objects in a container.'
    )
    lister.set_defaults(list=True)
    list_group = lister.add_mutually_exclusive_group(required=True)
    list_group.add_argument('-c',
                            '--container',
                            metavar='[CONTAINER]',
                            help='Target Container.',
                            default=None)
    list_group.add_argument('--all-containers',
                            action='store_true',
                            help='Target Container.',
                            default=None)
    lister.add_argument('--max-jobs',
                        metavar='[INT]',
                        default=None,
                        type=int,
                        help='Max number of processed on a single pass')
    lister.add_argument('--object-index',
                        metavar='[INT]',
                        help='Return the object from the index.',
                        type=int,
                        default=None)
    lister.add_argument('--filter',
                        metavar='[NAME]',
                        help='Filter returned list by name.',
                        default=None)

    # Provides for the list Function.
    updater = subparser.add_parser(
        'update',
        parents=[time_args, regex],
        help='Update Object headers from within a container.  This will'
             ' overwrite existing object headers with new ones as specified'
             ' on the command line.  See optional argment, "-OH"'
    )
    updater.set_defaults(update=True)
    update_group = updater.add_mutually_exclusive_group(required=True)
    update_group.add_argument('-c',
                              '--container',
                              metavar='[CONTAINER]',
                              help='Target Container.',
                              default=None)
    updater.add_argument('--max-jobs',
                         metavar='[INT]',
                         default=None,
                         type=int,
                         help='Max number of processed on a single pass')
    updater.add_argument('-o',
                         '--object',
                         metavar='[NAME]',
                         help='Target Object.',
                         default=None)
    updater.add_argument('--filter',
                         metavar='[NAME]',
                         help='Filter returned list by name.',
                         default=None)

    # Provides for the CDN Toggle Function.
    cdn_command = subparser.add_parser(
        'cdn-command',
        parents=[cdn_args],
        help='Run CDN Commands on a Container.'
    )
    cdn_command.set_defaults(cdn_command=True)
    cdn_command.add_argument('-c',
                             '--container',
                             metavar='[CONTAINER]',
                             help='Target Container.',
                             required=True,
                             default=None)

    cdn_command_group = cdn_command.add_mutually_exclusive_group(required=True)
    cdn_command_group.add_argument('--purge',
                                   metavar='[NAME]',
                                   help=('Purge a specific Object from the'
                                         ' CDN, This can be used multiple'
                                         ' times.'),
                                   default=[],
                                   action='append')
    cdn_command_group.add_argument('--enabled',
                                   action='store_true',
                                   default=None,
                                   help='Enable the CDN for a Container')
    cdn_command_group.add_argument('--disable',
                                   action='store_false',
                                   default=None,
                                   help='Disable the CDN for a Container')
