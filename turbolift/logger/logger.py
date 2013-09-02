# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import logging
import logging.handlers as lhs
import os

import turbolift as clds
from turbolift import info


class Logging(object):
    """Setup Application Logging."""

    def __init__(self, log_level, log_file=None):
        self.log_level = log_level
        self.log_file = log_file

    def logger_setup(self):
        """Setup logging for your application."""

        logger = logging.getLogger("%s" % (info.__appname__.upper()))

        avail_level = {'DEBUG': logging.DEBUG,
                       'INFO': logging.INFO,
                       'CRITICAL': logging.CRITICAL,
                       'WARN': logging.WARN,
                       'ERROR': logging.ERROR}

        _log_level = self.log_level.upper()
        if _log_level in avail_level:
            lvl = avail_level[_log_level]
            logger.setLevel(lvl)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s:%(levelname)s ==> %(message)s"
            )
        else:
            raise clds.NoLogLevelSet(
                'I died because you did not set a known log level'
            )

        if self.log_file:
            handler = lhs.RotatingFileHandler(self.log_file,
                                              maxBytes=150000000,
                                              backupCount=5)
        else:
            handler = logging.StreamHandler()

        handler.setLevel(lvl)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def return_logfile(filename):
    """Return a path for logging file.

    :param filename: name of the file for log storage.

    IF "/var/log/" does not exist, or you dont have write permissions to
    "/var/log/" the log file will be in your working directory
    Check for ROOT user if not log to working directory
    """

    if os.path.isfile(filename):
        return filename
    else:
        user = os.getuid()
        logname = ('%s' % filename)
        logfile = os.path.join(os.getenv('HOME'), logname)
        return logfile


def load_in(log_level='info'):
    """Load in the log handler.

    If output is not None, systen will use the default
    Log facility.
    """

    _file = '%s.log' % info.__appname__
    _log_file = return_logfile(filename=_file)
    log = Logging(log_level=log_level, log_file=_log_file)
    output = log.logger_setup()
    return output
