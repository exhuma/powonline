import unittest


class TestUtil(unittest.TestCase):

    def test_import(self):
        '''
        Currently this module only has global-level stuff.

        Just test that importing works without a hitch
        '''
        from powonline import util
