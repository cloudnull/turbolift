# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
LOG = None
ARGS = None


def load_constants(log_method, args):
    """Setup In Memory Persistent Logging.

    :param log_method: Set method for logging
    :param args: Arguments that have been parsed for in application use.
    """

    global LOG, ARGS
    LOG = log_method
    ARGS = args


def start_work():
    """Begin Work."""

    def get_method(method, name):
        """Import what is required to run the System."""

        to_import = '%s.%s' % (method.__name__, name)
        return __import__(to_import, fromlist="None")

    def get_actions(module, name):
        """Get all available actions from an imported method.

        :param module:
        :param name:
        :return method attributes:
        """

        return getattr(module, name)

    import pkgutil

    import turbolift as clds
    from turbolift import methods as met
    from turbolift import utils
    from turbolift.authentication import authentication as auth


    try:
        for mod, name, package in pkgutil.iter_modules(met.__path__):
            if ARGS.get(name) is not None:
                method = get_method(method=met, name=name)
                actions = get_actions(module=method, name=name)
                actions(auth=auth.authenticate()).start()
                break
        else:
            raise clds.SystemProblem('No Method set for processing')
    except KeyboardInterrupt:
        utils.emergency_exit(msg='Caught KeyboardInterrupt, I\'M ON FIRE!!!!')