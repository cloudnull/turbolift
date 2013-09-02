# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def optional_args(parser):
    """Add in all optional Arguments."""

    optionals = parser.add_argument_group('Additional Options',
                                          'Things you might want to'
                                          ' add to your operation')
    optionals.add_argument('-P',
                           '--preserve-path',
                           action='store_true',
                           help=('This will preserve the full path to a file'
                                 ' when uploaded to a container.'))
    optionals.add_argument('-I',
                           '--internal',
                           action='store_true',
                           help='Use Service Network')
    optionals.add_argument('--error-retry',
                           metavar='[ATTEMPTS]',
                           type=int,
                           default=5,
                           help=('This option sets the number of attempts'
                                 ' %(prog)s will attempt an operation'
                                 ' before quiting. The default is 5. This'
                                 ' is useful if you have a spotty'
                                 ' network or ISP.'))
    optionals.add_argument('--cc',
                           metavar='[CONCURRENCY]',
                           type=int,
                           default=50,
                           help='Upload Concurrency')
    optionals.add_argument('--system-config',
                           metavar='[CONFIG-FILE]',
                           type=str,
                           default=None,
                           help=('Path to your Configuration file. This is'
                                 ' an optional argument used to spec '
                                 ' credentials.'))
    optionals.add_argument('--quiet',
                           action='store_true',
                           help='Make %(prog)s Shut the hell up')
    optionals.add_argument('--verbose',
                           action='store_true',
                           help='Be verbose While Uploading')
    optionals.add_argument('--debug',
                           action='store_true',
                           help='Turn up verbosity to over 9000')
