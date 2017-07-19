import unittest
import re
import FileCopyUtil

class TestFileCopyUtil(unittest.TestCase):

	def test_regex(self):
		pos_test = ['550', 'scans550_01', '00550.txt', 't2scans550_01']
		neg_test = ['something completely off', '5500', 'scans1550', '5501.txt']
		mrn = '550'

		for filename in pos_test:
			self.assertTrue(FileCopyUtil._mrn_in_name(mrn, filename))
		for filename in neg_test:
			self.assertFalse(FileCopyUtil._mrn_in_name(mrn, filename))

if __name__ == '__main__':
	unittest.main()