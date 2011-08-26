import sys
import unittest
import pickle
from raisin.restyler.resource import Resource
from raisin.restyler.config import PICKLED
from raisin.restyler.config import CSV
MARKER = "ABCDEFGHIFKLMNOPQRSTUVWXYZ"


class DummyResourceProvider:

    def get(self, uri, content_type):
        if content_type == PICKLED:
            return pickle.dumps(MARKER)
        else:
            return MARKER


class ResourceTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_get_unknown_resource(self):
        dummyresourceprovider = DummyResourceProvider()
        resource = Resource(dummyresourceprovider)
        self.failUnlessRaises(KeyError, resource.get, "UNKNOWN")

    def test_get_pickled_resource(self):
        dummyresourceprovider = DummyResourceProvider()
        resource = Resource(dummyresourceprovider)
        projects = resource.get("project_projects")
        self.failUnless(projects == MARKER)

    def test_get_csv_resource(self):
        dummyresourceprovider = DummyResourceProvider()
        resource = Resource(dummyresourceprovider)
        projects = resource.get("project_projects", CSV)
        self.failUnless(projects == MARKER)


# make the test suite.
def suite():
    loader = unittest.TestLoader()
    testsuite = loader.loadTestsFromTestCase(ResourceTest)
    return testsuite


# Make the test suite; run the tests.
def test_main():
    testsuite = suite()
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    runner.run(testsuite)

if __name__ == "__main__":
    test_main()
