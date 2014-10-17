# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import datetime
import os
import tempfile
import unittest

import mock

import turbolift
from turbolift.utils import basic_utils


class TestAuthenticate(unittest.TestCase):
    """Test Basic Utils Methods."""

    def setUp(self):
        pass

    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, obj, cls, msg=None):
            if not isinstance(obj, cls):
                standardMsg = '%s is not an instance of %r' % (obj, cls)
                self.fail(self._formatMessage(msg, standardMsg))

    def test_time_stamp(self):
        fmt, date, date_delta, now = basic_utils.time_stamp()
        self.assertEqual('%Y-%m-%dT%H:%M:%S.%f', fmt)
        self.assertIsInstance(date, type)
        self.assertIsInstance(date_delta, type)
        self.assertIsInstance(now, datetime.datetime)

    def test_json_encode(self):
        json_dict = '{"key": "value"}'
        self.assertIsInstance(basic_utils.json_encode(read=json_dict), dict)

    def test_unique_list_dicts(self):
        dict_list = [
            {'key': 'value'},
            {'key': 'value'}
        ]
        return_list = basic_utils.unique_list_dicts(dlist=dict_list, key='key')
        self.assertEqual(len(return_list), 1)

    def test_dict_pop_none(self):
        dict_with_none = {
            'key': 'value',
            'test': None
        }
        return_dict = basic_utils.dict_pop_none(dictionary=dict_with_none)
        if 'test' in return_dict:
            self.fail(
                'None Value not removed from dictionary'
            )

    def test_jpath(self):
        return_path = basic_utils.jpath(root='/test', inode='path/of/test')
        self.assertEqual(return_path, '/test/path/of/test')

    def test_rand_string(self):
        return_str1 = basic_utils.rand_string()
        return_str2 = basic_utils.rand_string()
        self.assertIsInstance(return_str1, str)
        self.assertIsInstance(return_str2, str)
        self.assertNotEqual(return_str1, return_str2)

    def test_create_tmp(self):
        return_file = basic_utils.create_tmp()
        if not os.path.exists(return_file):
            self.fail('No File was found when creating a temp file')
        else:
            try:
                os.remove(return_file)
            except OSError:
                pass

    def test_remove_file(self):
        return_file = tempfile.mkstemp()[1]
        basic_utils.remove_file(filename=return_file)
        if os.path.exists(return_file):
            self.fail('Failed to remove File')

    def test_file_exists(self):
        return_file = tempfile.mkstemp()[1]
        self.assertEqual(
            basic_utils.file_exists(filename=return_file), True
        )
        try:
            os.remove(return_file)
        except OSError:
            pass
        else:
            self.assertEqual(
                basic_utils.file_exists(filename=return_file), False
            )

    @mock.patch('turbolift.utils.basic_utils.turbo.ARGS', {'batch_size': 1})
    @mock.patch('turbolift.utils.basic_utils.report.reporter')
    def test_batcher(self, mock_reporter):
        return_batch_size = basic_utils.batcher(1)
        self.assertEqual(return_batch_size, 1)
        self.assertTrue(mock_reporter.called)

    @mock.patch('turbolift.utils.basic_utils.turbo.ARGS', {'batch_size': 1})
    @mock.patch('turbolift.utils.basic_utils.report.reporter')
    def test_batcher_with_more_files(self, mock_reporter):
        return_batch_size = basic_utils.batcher(2)
        self.assertEqual(return_batch_size, 1)
        self.assertTrue(mock_reporter.called)

    def test_collision(self):
        self.assertEqual(basic_utils.collision_rename('test'), 'test')

    def test_collision_rename_directory(self):
        dir_name = tempfile.mkdtemp()
        dir_rename = basic_utils.collision_rename(dir_name)
        self.assertEqual('%s.renamed' % dir_name, dir_rename)
        os.removedirs(dir_name)

    def test_mkdir_p(self):
        dir_name = tempfile.mkdtemp()
        if not os.path.exists(dir_name):
            self.fail('Failed to create base directory')
        else:
            long_dir_name = os.path.join(dir_name, 'test/path')
            basic_utils.mkdir_p(long_dir_name)
            if not os.path.exists(long_dir_name):
                self.fail('Failed to create recursive directories.')

    def test_mkdir_p_failure(self):
        os = mock.Mock(side_effect=OSError('TEST EXCEPTION'))
        with mock.patch('turbolift.utils.basic_utils.os.makedirs', os):
            self.assertRaises(
                turbolift.DirectoryFailure, basic_utils.mkdir_p, 'test'
            )

    def test_set_unique_dirs(self):
        fake_object_list = [
            'testone/1',
            'testone/1',
            'testtwo/2',
            'testtwo/2',
            'testthree/3'
        ]
        return_object_list = basic_utils.set_unique_dirs(
            object_list=fake_object_list, root_dir='/test/dir/'
        )
        self.assertNotEqual(len(fake_object_list), len(return_object_list))

    def test_get_sfile_with_preserver_path(self):
        args = {'preserve_path': True}
        with mock.patch('turbolift.utils.basic_utils.turbo.ARGS', args):
            obj = basic_utils.get_sfile(ufile='object1', source='test/dir')
            self.assertEqual(obj, 'test/dir/object1')

    @mock.patch('turbolift.utils.basic_utils.turbo.ARGS', {})
    def test_get_sfile_isfile(self):
        os = mock.Mock().return_value(True)
        with mock.patch('turbolift.utils.basic_utils.os.path.isfile', os):
            obj = basic_utils.get_sfile(ufile='object1', source='test/dir')
            self.assertEqual(obj, 'dir')

    @mock.patch('turbolift.utils.basic_utils.turbo.ARGS', {})
    def test_get_sfile_dot_source(self):
        def fake_cwd():
            return '/some/dir'

        with mock.patch('turbolift.utils.basic_utils.os.getcwd', fake_cwd):
            obj = basic_utils.get_sfile(ufile='object1', source='.')
            self.assertEqual(obj, '/some/dir')

    @mock.patch('turbolift.utils.basic_utils.turbo.ARGS', {})
    def test_get_sfile_dot_source(self):
        obj = basic_utils.get_sfile(ufile='/test/object1', source='/test')
        self.assertEqual(obj, 'object1')

    def test_real_full_path_relitive_path(self):
        os.environ['HOME'] = '/home/test'
        obj = basic_utils.real_full_path(object='~/test/dir')
        self.assertEqual(obj, '/home/test/test/dir')

    def test_real_full_path(self):
        obj = basic_utils.real_full_path(object='/test/dir')
        self.assertEqual(obj, '/test/dir')

    # def test_get_local_source(self):
    #     self.fail('no test made yet')
    #
    # def test_ustr(self):
    #     self.fail('no test made yet')
    #
    # def test_retryloop(self):
    #     self.fail('no test made yet')
    #
    # def test_restor_perms(self):
    #     self.fail('no test made yet')
    #
    # def test_stat_file(self):
    #     self.fail('no test made yet')
    #
    # def test_stupid_hack(self):
    #     self.fail('no test made yet')
    #
    # def test_match_filter(self):
    #     self.fail('no test made yet')
