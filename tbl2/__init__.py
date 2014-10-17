# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import signal

ARGS = None


class NoLogLevelSet(Exception):
    """Not Log Level Set Exception."""

    pass


class NoSource(Exception):
    """No Source Exception."""

    pass


class AuthenticationProblem(Exception):
    """Authentication Problem Exception."""

    pass


class SystemProblem(Exception):
    """System Problem Exception."""

    pass


class DirectoryFailure(Exception):
    """Directory Failure Exception."""

    pass


class RetryError(Exception):
    """Retry Error Exception."""

    pass


class NoFileProvided(Exception):
    """No File Provided Exception."""

    pass


class NoTenantIdFound(Exception):
    """No Tenant ID was found."""

    pass


def emergency_kill(reclaim=None):
    """Exit process.

    :return kill pid:
    """

    if reclaim is not None:
        return os.kill(os.getpid(), signal.SIGKILL)
    else:
        return os.kill(os.getpid(), signal.SIGCHLD)


def emergency_exit(msg):
    """Exit process.

    :param msg:
    :return exit.status:
    """

    raise SystemExit(msg)


def load_constants(args):
    """Setup In Memory Persistent Logging.

    :param args: Arguments that have been parsed for in application use.
    """

    global ARGS
    ARGS = args
