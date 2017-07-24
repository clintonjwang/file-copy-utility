import unittest
import re
import FileCopyUtil

class TestFileCopyUtil(unittest.TestCase):

	def test_match_mrn(self):
		pos_test = ['55081', 'scans55081_01', '0055081.txt', 't2scans55081-01']
		neg_test = ['something completely off', '550810', 'scans155081', '550811.txt']
		mrn = '55081'

		for filename in pos_test:
			self.assertTrue(FileCopyUtil._mrn_in_name(mrn, filename))
		for filename in neg_test:
			self.assertFalse(FileCopyUtil._mrn_in_name(mrn, filename))

	def test_looks_like_mrn(self):
		pos_test = ['5508141', 'scans1234567_01', '0508141.txt', '5508141_01']
		neg_test = ['something completely off', 't2scans_0001', 'scans20161004', '05-19-17.txt']

		for filename in pos_test:
			self.assertTrue(FileCopyUtil._name_has_mrn(filename))
		for filename in neg_test:
			self.assertFalse(FileCopyUtil._name_has_mrn(filename))

	def test_has_different_mrn(self):
		pos_test = ['5508141', 'scans1234567_01', '0508141.txt', '5508141_01']
		neg_test = ['something completely off', '55081', 'scans20161004', 't2scans55081-01']
		mrns = [55081]

		for filename in pos_test:
			self.assertTrue(FileCopyUtil._has_different_mrn(filename, mrns))
		for filename in neg_test:
			self.assertFalse(FileCopyUtil._has_different_mrn(filename, mrns))

if __name__ == '__main__':
	unittest.main()