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
from logging import handlers
import os


"""Example Usage:
>>> from cloudlib import logger
>>> log = logger.LogSetup()
>>> log.default_logger(name='test_logger')

>>> # The following can then be placed in any module that you like
>>> # Just use the name of the logger you created
>>> from cloudlib import logger
>>> LOG = logger.getLogger(name='test_logger')
>>> LOG.info('This is a test message')
"""


def getLogger(name):
    """Return a logger from a given name.

    If the name does not have a log handler, this will create one for it based
    on the module name which will log everything to a log file in a location
    the executing user will have access to.

    :param name: ``str``
    :return: ``object``
    """
    log = logging.getLogger(name=name)
    for handler in log.handlers:
        if name == handler.name:
            return log
    else:
        return LogSetup().default_logger(name.split('.')[0])


class LogSetup(object):

    def __init__(self, max_size=500, max_backup=5, debug_logging=False,
                 log_dir='/var/log', log_name=__name__):
        """Setup Logging.

        :param max_size: ``int``
        :param max_backup: ``int``
        :param debug_logging: ``bol``
        :param log_dir: ``str``
        :param log_name: ``str``
        """
        self.max_size = (max_size * 1024 * 1024)
        self.max_backup = max_backup
        self.debug_logging = debug_logging
        self.format = None
        self.name = log_name
        self.log_dir = log_dir

    def default_logger(self, enable_stream=False, enable_file=True):
        """Default Logger.

        This is set to use a rotating File handler and a stream handler.
        If you use this logger all logged output that is INFO and above will
        be logged, unless debug_logging is set then everything is logged.
        The logger will send the same data to a stdout as it does to the
        specified log file.

        You can disable the default handlers by setting either `enable_file` or
        `enable_stream` to `False`

        :param enable_stream: ``bol``
        :param enable_file: ``bol``
        :return: ``object``
        """
        if self.format is None:
            self.format = logging.Formatter(
                '%(asctime)s - %(module)s:%(levelname)s => %(message)s'
            )

        log = logging.getLogger('turbolift')

        if enable_file is True:
            log_file_name = self.name
            if not log_file_name.endswith('log'):
                log_file_name = '%s.log' % log_file_name

            log_file = self.return_logfile(
                filename=log_file_name, log_dir=self.log_dir
            )
            file_handler = handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=self.max_size,
                backupCount=self.max_backup
            )
            self.set_handler(log, handler=file_handler)

        if enable_stream is True or self.debug_logging is True:
            stream_handler = logging.StreamHandler()
            self.set_handler(log, handler=stream_handler)

        log.debug('Logger [ %s ] loaded', self.name)
        return getLogger('turbolift')

    def set_handler(self, log, handler):
        """Set the logging level as well as the handlers.

        :param log: ``object``
        :param handler: ``object``
        """

        if self.debug_logging is True:
            log.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)

        handler.name = 'turbolift'
        handler.setFormatter(self.format)
        log.addHandler(handler)

    @staticmethod
    def return_logfile(filename, log_dir):
        """Return a path for logging file.

        If ``log_dir`` exists and the userID is 0 the log file will be written
        to the provided log directory. If the UserID is not 0 or log_dir does
        not exist the log file will be written to the users home folder.

        :param filename: ``str``
        :param log_dir: ``str``
        :return: ``str``
        """
        user = os.getuid()
        home = os.getenv('HOME')
        default_log_location = os.path.join(home, filename)
        if not user == 0:
            return default_log_location
        else:
            if os.path.isdir(log_dir):
                return os.path.join(log_dir, filename)
            else:
                return default_log_location