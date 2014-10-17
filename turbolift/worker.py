# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

from cloudlib import logger

from turbolift import utils
from turbolift.authentication import auth
from turbolift import exceptions


LOG = logger.getLogger('turbolift')


class Worker(object):
    def __init__(self, job_name, job_args):
        self.job_name = job_name
        self.job_args = job_args
        self.job_map = {
            'archive': '',
            'cdn': 'turbolift.methods.cdn_command.CdnRunMethod',
            'clone': '',
            'delete': 'turbolift.methods.delete_items.DeleteRunMethod',
            'download': '',
            'list': 'turbolift.methods.list_items.ListRunMethod',
            'show': 'turbolift.methods.show_items.ShowRunMethod',
            'update': 'turbolift.methods.update_items.UpdateRunMethod',
            'upload': 'turbolift.methods.upload_items.UploadRunMethod',
        }

    @staticmethod
    def _get_method(method):
        """Return an imported object."""

        module = method.split('.')
        module_import = __import__(
            '.'.join(module[:-1]),
            fromlist=module[-1:]
        )
        return getattr(module_import, module[-1])

    @staticmethod
    def _str_headers(header):
        """Retrun a dict from a 'KEY=VALUE' string."""

        return dict(header.spit('='))

    @staticmethod
    def _list_headers(headers):
        """Return a dict from a list of KEY=VALUE strings.

        :param headers: ``list``
        """

        return dict([_kv.split('=') for _kv in headers])

    def run_manager(self, job_override=None):
        """The run manager."""

        for arg_name, arg_value in self.job_args.iteritems():
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

        indicator_options = {
            'debug': self.job_args.get('debug'),
            'quiet': self.job_args.get('quiet'),
            'msg': ' Authenticating... '
        }
        with utils.IndicatorThread(**indicator_options):
            LOG.debug('Authenticate against the Service API')
            self.job_args.update(auth.authenticate(job_args=self.job_args))

        try:
            if job_override:
                action = self._get_method(method=job_override)
            else:
                job = self.job_map[self.job_args['parsed_command']]
                action = self._get_method(method=job)

            run = action(job_args=self.job_args)
        except KeyboardInterrupt:
            exceptions.emergency_kill(reclaim=True)
        else:
            run.start()
