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

    def test_keys2dict(self):
        list_of_strings = ['test=value']
        return_dict = basic_utils.keys2dict(chl=list_of_strings)
        self.assertIsInstance(return_dict, dict)

    def test_keys2dict_with_none_value(self):
        list_of_strings = None
        return_dict = basic_utils.keys2dict(chl=list_of_strings)
        self.assertEqual(return_dict, None)

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

    # def test_batch_gen(self):
    #     self.fail('no test made yet')
    #
    # def test_collision_rename(self):
    #     self.fail('no test made yet')
    #
    # def test_mkdir_p(self):
    #     self.fail('no test made yet')
    #
    # def test_set_unique_dirs(self):
    #     self.fail('no test made yet')
    #
    # def test_get_sfile(self):
    #     self.fail('no test made yet')
    #
    # def test_real_full_path(self):
    #     self.fail('no test made yet')
    #
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
