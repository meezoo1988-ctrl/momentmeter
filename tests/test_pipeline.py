import copy
import unittest
import momentmeter as m

class Validation(unittest.TestCase):
    def setUp(self): self.job = m.load('first-short')
    def test_draft(self): self.assertTrue(70 <= m.validate(self.job, True) <= 100)
    def test_missing_rights_block_production(self):
        with self.assertRaises(ValueError): m.validate(self.job)
    def test_traversal_blocked(self):
        self.job['clips'][0]['file'] = '../secret'
        with self.assertRaises(ValueError): m.validate(self.job, True)
    def test_wrong_order_blocked(self):
        self.job['clips'][0]['rank'] = 1
        with self.assertRaises(ValueError): m.validate(self.job, True)
    def test_empty_commentary_blocked(self):
        self.job['clips'][0]['narration'] = ''
        with self.assertRaises(ValueError): m.validate(self.job, True)

if __name__ == '__main__': unittest.main()
