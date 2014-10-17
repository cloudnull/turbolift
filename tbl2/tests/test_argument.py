# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import inspect
import sys

from tbl2 import arguments


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock


class ArguementsTests(unittest.TestCase):
    """Test all of the arguments."""

    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, obj, cls, msg=None):
            if not isinstance(obj, cls):
                standardMsg = '%s is not an instance of %r' % (obj, cls)
                self.fail(self._formatMessage(msg, standardMsg))

    def setUp(self):
        self.args = arguments.args_setup()
        self.command = sys.argv[0]
        self.arg_dict = {'os_user': 'TEST-USER',
                         'container': 'TEST-CONTAINER'}

    def auth_rax_args(self):
        auth_dict = {
            'os_password': 'TEST-PASSWORD',
            'os_rax_auth': 'TEST-REGION'
        }
        auth_dict.update(self.arg_dict)
        return auth_dict

    def auth_hp_args(self):
        auth_dict = {
            'os_apikey': 'TEST-KEY',
            'os_hp_auth': 'TEST-REGION'
        }
        auth_dict.update(self.arg_dict)
        return auth_dict

    def auth_basic_args(self):
        auth_dict = {
            'os_password': 'TEST-KEY',
            'os_region': 'TEST-REGION',
            'os_auth_url': 'https://test.url'
        }
        auth_dict.update(self.arg_dict)
        return auth_dict

    def check_auth_types(self):
        methods = inspect.getmembers(
            object=self,
            predicate=inspect.ismethod
        )
        for name, method in methods:
            if name.startswith('auth'):
                args = method()
                self.assertIsInstance(args, dict)

                parsed_args = arguments.understand_args(set_args=args)
                self.args.set_defaults(**parsed_args)

    def test_understanding_failure_no_apikey_or_password(self):
        base_dict = {
            'os_user': 'TEST-USER',
            'os_auth_url': 'https://test.url',
            'os_region': 'TEST-REGION',
        }
        self.assertRaises(
            SystemExit,
            arguments.understand_args,
            base_dict
        )

    def test_understanding_failure_no_user(self):
        base_dict = {
            'os_password': 'TEST-KEY',
            'os_auth_url': 'https://test.url',
            'os_region': 'TEST-REGION'
        }
        self.assertRaises(
            SystemExit,
            arguments.understand_args,
            base_dict
        )

    def test_understanding_region_upper(self):
        base_dict = {
            'os_user': 'TEST-USER',
            'os_password': 'TEST-KEY',
            'os_auth_url': 'https://test.url',
            'os_region': 'lower-region'
        }
        understood = arguments.understand_args(set_args=base_dict)
        self.assertEqual(
            first=understood['os_region'],
            second=base_dict['os_region'].upper()
        )

    def test_understanding_rax_auth_upper(self):
        base_dict = {
            'os_user': 'TEST-USER',
            'os_password': 'TEST-KEY',
            'os_auth_url': 'https://test.url',
            'os_rax_auth': 'lower-region'
        }
        understood = arguments.understand_args(set_args=base_dict)
        self.assertEqual(
            first=understood['os_rax_auth'],
            second=base_dict['os_rax_auth'].upper()
        )

    def test_method_archive(self):
        base = [self.command,
                'archive',
                '--source',
                'TEST-SOURCE',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_delete(self):
        base = [self.command,
                'delete',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_download(self):
        base = [self.command,
                'download',
                '--source',
                'TEST-SOURCE',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_upload(self):
        base = [self.command,
                'upload',
                '--source',
                'TEST-SOURCE',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_show(self):
        base = [self.command,
                'show',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_list(self):
        base = [self.command,
                'list',
                '--container',
                'TEST-CONTAINER']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_cdn_command(self):
        base = [self.command,
                'cdn-command',
                '--container',
                'TEST-CONTAINER',
                '--enabled']

        with mock.patch('sys.argv', base):
            self.check_auth_types()

    def test_method_clone(self):
        base = [self.command,
                'clone',
                '--source-container',
                'TEST-SOURCE',
                '--target-container',
                'TEST-CONTAINER',
                '--target-region',
                'TEST-TARGET-REGION']

        with mock.patch('sys.argv', base):
            self.check_auth_types()
