# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from turbolift import ARGS


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

    # Low imports for load in module.
    import pkgutil

    # Low imports for load in module.
    import turbolift as turbo
    from turbolift.authentication import auth as auth
    from turbolift import methods as met

    try:
        for mod, name, package in pkgutil.iter_modules(met.__path__):
            if ARGS.get(name) is not None:
                titled_name = name.title().replace('_', '')
                method = get_method(method=met, name=name)
                actions = get_actions(module=method, name=titled_name)
                actions(auth=auth.authenticate()).start()
                break
        else:
            raise turbo.SystemProblem('No Method set for processing')
    except KeyboardInterrupt:
        turbo.emergency_kill(reclaim=True)
