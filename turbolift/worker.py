# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

from cloudlib import logger
from cloudlib import indicator

from turbolift.authentication import auth
from turbolift import exceptions


LOG = logger.getLogger('turbolift')


class Worker(object):
    def __init__(self, job_args):
        self.job_args = job_args
        self.job_map = {
            'archive': 'turbolift.methods.archive:ArchiveRunMethod',
            'cdn': 'turbolift.methods.cdn_command:CdnRunMethod',
            'clone': 'turbolift.methods.clone:CloneRunMethod',
            'delete': 'turbolift.methods.delete_items:DeleteRunMethod',
            'download': 'turbolift.methods.download:DownloadRunMethod',
            'list': 'turbolift.methods.list_items:ListRunMethod',
            'show': 'turbolift.methods.show_items:ShowRunMethod',
            'update': 'turbolift.methods.update_items:UpdateRunMethod',
            'upload': 'turbolift.methods.upload_items:UploadRunMethod',
        }

    @staticmethod
    def _get_method(method):
        """Return an imported object.

        :param method: ``str`` DOT notation for import with Colin used to
                               separate the class used for the job.
        :returns: ``object`` Loaded class object from imported method.
        """

        # Split the class out from the job
        module = method.split(':')

        # Set the import module
        _module_import = module[0]

        # Set the class name to use
        class_name = module[-1]

        # import the module
        module_import = __import__(_module_import, fromlist=[class_name])

        # Return the attributes for the imported module and class
        return getattr(module_import, class_name)

    @staticmethod
    def _str_headers(header):
        """Return a dict from a 'KEY=VALUE' string.

        :param header: ``str``
        :returns: ``dict``
        """

        return dict(header.spit('='))

    @staticmethod
    def _list_headers(headers):
        """Return a dict from a list of KEY=VALUE strings.

        :param headers: ``list``
        :returns: ``dict``
        """

        return dict([_kv.split('=') for _kv in headers])

    def run_manager(self, job_override=None):
        """The run manager.

        The run manager is responsible for loading the plugin required based on
        what the user has inputted using the parsed_command value as found in
        the job_args dict. If the user provides a *job_override* the method
        will attempt to import the module and class as provided by the user.

        Before the method attempts to run any job the run manager will first
        authenticate to the the cloud provider.

        :param job_override: ``str`` DOT notation for import with Colin used to
                                     separate the class used for the job.
        """

        for arg_name, arg_value in self.job_args.items():
            if arg_name.endswith('_headers'):
                if isinstance(arg_value, list):
                    self.job_args[arg_name] = self._list_headers(
                        headers=arg_value
                    )
                elif not arg_name:
                    self.job_args[arg_name] = self._str_headers(
                        header=arg_value
                    )
                else:
                    self.job_args[arg_name] = dict()

        # Set base header for the user-agent
        self.job_args['base_headers']['User-Agent'] = 'turbolift'

        LOG.info('Authenticating')
        indicator_options = {'run': self.job_args.get('run_indicator', True)}
        with indicator.Spinner(**indicator_options):
            LOG.debug('Authenticate against the Service API')
            self.job_args.update(auth.authenticate(job_args=self.job_args))

        if job_override:
            action = self._get_method(method=job_override)
        else:
            parsed_command = self.job_args.get('parsed_command')
            if not parsed_command:
                raise exceptions.NoCommandProvided(
                    'Please provide a command. Basic commands are: %s',
                    list(self.job_map.keys())
                )
            else:
                action = self._get_method(method=self.job_map[parsed_command])

        run = action(job_args=self.job_args)
        run.start()
