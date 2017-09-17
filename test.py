#!/usr/bin/env python

import unittest

from lib import qif
import datetime


class TestQIF(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_qif_name(self):

        name = qif.get_qif_name(
            datetime.datetime(2010, 1, 1, 00, 00, 00),
            datetime.datetime(2012, 4, 13, 00, 00, 00)
        )
        self.assertEqual(name, '2010.01.01 - 2012.04.13.qif')

    def test_is_file_present(self):

        found = qif.is_file_present('lib/db.py')
        self.assertTrue(found)

        found = qif.is_file_present('test.py')
        self.assertTrue(found)

        found = qif.is_file_present('./test.py')
        self.assertTrue(found)

        not_found = qif.is_file_present('aaa/bbb/ccc/test.py')
        self.assertFalse(not_found)

    def test_get_available_name(self):

        name = qif.get_available_name('lib/db.py')
        self.assertEqual(name, 'lib/db.py.1')


if __name__ == '__main__':
    unittest.main()
