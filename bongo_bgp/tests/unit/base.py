import mock


class BaseTestCase(object):
    def assertIsNone(self, item):
        self.assertEqual(None, item)

    def assertFalse(self, item):
        self.assertEqual(False, item)

    def assertTrue(self, item):
        self.assertEqual(True, item)

    def assertEqual(self, l, r):
        if l != r:
            raise AssertionError("%s != %s" % (l, r))

    def assertIn(self, needle, haystack):
        if needle not in haystack:
            raise AssertionError("%s not in %s" % (needle, haystack))

    def teardown_method(self, test_method):
        mock.patch.stopall()
