# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import signal

from cloudlib import logger
from turbolift import utils


LOG = logger.getLogger('turbolift')


class _BaseException(Exception):
    def __init__(self, *args):
        if len(args) > 1:
            format_message = args[0]
            try:
                message = format_message % tuple(args[1:])
            except TypeError as exp:
                message = (
                    'The exception message was not formatting correctly.'
                    ' Error: [ %s ]. This was the data passed: "%s"'
                    % (exp, args)
                )
        else:
            message = args[0]

        super(_BaseException, self).__init__(message)
        LOG.error(message)


class NoCommandProvided(_BaseException):
    """No command was provided Exception."""

    pass


class NoSource(_BaseException):
    """No Source Exception."""

    pass


class AuthenticationProblem(_BaseException):
    """Authentication Problem Exception."""

    pass


class SystemProblem(_BaseException):
    """System Problem Exception."""

    pass


class DirectoryFailure(_BaseException):
    """Directory Failure Exception."""

    pass


class RetryError(_BaseException):
    """Retry Error Exception."""

    pass


class NoFileProvided(_BaseException):
    """No File Provided Exception."""

    pass


class NoTenantIdFound(_BaseException):
    """No Tenant ID was found."""

    pass


def emergency_kill():
    """Exit process.

    :return kill pid:
    """

    os.kill(os.getpid(), signal.SIGKILL)


def emergency_exit(msg):
    """Exit process.

    :param msg:
    :return exit.status:
    """

    raise SystemExit(msg)
