import sys
import unittest
from raisin.restyler import page
from pyramid.testing import DummyRequest


class MatchedRoute(object):
    pass


class ResourceTest(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_page(self):
        request = DummyRequest()

        class DummyRoute(object):
            name = 'p1_homepage'
        route = DummyRoute()
        request.matched_route = route
        page.Page(request)

    def test_get_breadcrumbs_1(self):
        """No layout, no breadcrumbs"""
        request = DummyRequest()
        request.matched_route = MatchedRoute()
        request.matched_route.name = 'p1_homepage'
        p = page.Page(request)
        self.failUnless(p.get_breadcrumbs(request) == None)

    def test_get_breadcrumbs_2(self):
        request = DummyRequest()
        request.matched_route = MatchedRoute()
        request.matched_route.name = 'p1_project'
        request.matchdict = {'project_name': 'ENCODE'}
        p = page.Page(request)
        breadcrumbs = [{'url': 'http://example.com/',
                        'title': 'Projects'}]
        self.failUnless(p.get_breadcrumbs(request) == breadcrumbs)

    def test_get_breadcrumbs_3(self):
        request = DummyRequest()
        request.matched_route = MatchedRoute()
        request.matched_route.name = 'p1_replicate'
        request.matchdict = {'project_name': 'ENCODE',
                             'replicate_name': 'Ging001N',
                             'parameter_list': None,
                             'parameter_values': None,
                             'tab_name': None}
        p = page.Page(request)
        bcr = [{'url': 'http://example.com/',
                'title': 'Projects'},
               {'url': 'http://example.com/project/ENCODE/tab/experiments/',
                'title': 'Project: ENCODE'},
               {'url': 'http://example.com/project/ENCODE/None/None/tab/None',
                'title': 'Experiment: None'}]
        print p.get_breadcrumbs(request)
        self.failUnless(p.get_breadcrumbs(request) == bcr)


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
