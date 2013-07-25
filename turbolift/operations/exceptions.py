# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


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
