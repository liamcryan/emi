import os
import unittest
from requests import Response, PreparedRequest
from requests.adapters import HTTPAdapter
from requests_html import HTMLSession
from emi.api import MethodMock, MaxDepthExceeded

htmlsession_get = MethodMock(method=HTMLSession.get)
HTMLSession.get = htmlsession_get.mock
MethodMock.directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures')


def get_http_response(*args, **get_kwargs):
    with HTMLSession() as s:
        s.verify = False
        r = s.get(*args, **get_kwargs)
        if not r.ok:
            raise Exception('unable to get url1: {}'.format(*args))
        return r


class TestHTTPResponses(unittest.TestCase):
    url1 = 'https://google.com'

    @staticmethod
    def clean_up():
        for file in os.listdir(MethodMock.directory):
            if file == '.gitkeep':
                continue
            os.remove(os.path.join(MethodMock.directory, file))

    @classmethod
    def setUpClass(cls):
        cls.clean_up()

    @classmethod
    def tearDownClass(cls):
        cls.clean_up()

    @htmlsession_get.activate
    def test_retrieve_http_pickle(self):
        """ test that the http response you receive is the same as (close to) the pickled response"""
        http_response1 = get_http_response(self.url1)
        pickled_response1 = htmlsession_get.get_method_response(1)
        for attr in http_response1.__dict__:
            if attr == '__getstate__':
                continue
            elif attr == 'raw':
                assert pickled_response1.raw is None
            elif attr == 'history':
                assert isinstance(pickled_response1.history[0], Response)
            elif attr == 'request':
                assert isinstance(pickled_response1.request, PreparedRequest)
            elif attr == 'session':
                assert isinstance(pickled_response1.session, HTMLSession)
            elif attr == 'connection':
                assert isinstance(pickled_response1.connection, HTTPAdapter)
            else:
                assert http_response1.__getattribute__(attr) == pickled_response1.__getattribute__(attr)

    @htmlsession_get.activate
    def test_retrieve_two_identical_http_calls_different_pickles(self):
        """ sometimes you expect different results from separate calls to the same function/args/kwargs.

        test that multiple calls to the same function/args/kwargs provide separate pickled results.
        """
        http_response1 = get_http_response(self.url1)
        http_response2 = get_http_response(self.url1)
        pickled_response1 = htmlsession_get.get_method_response(1)
        pickled_response2 = htmlsession_get.get_method_response(2)
        assert http_response1.elapsed == pickled_response1.elapsed
        assert http_response2.elapsed == pickled_response2.elapsed

    @htmlsession_get.activate
    def test_find_the_object(self):
        class A(object):
            def __init__(self, session):
                self.a0 = 0
                self.a1 = HTTPAdapter
                self.b = B(session)

        class B(object):
            def __init__(self, session):
                self.b0 = 'zero'
                self.b1 = PreparedRequest
                self.c = C(session)

        class C(object):
            def __init__(self, session):
                self.c = session

        with HTMLSession() as s:
            a = A(session=s)
            try:
                htmlsession_get._find_the_object_in_f_locals_bfs(f_locals={'a': a, 'b': {}}, max_depth=2)
                raise Exception
            except MaxDepthExceeded:
                obj = htmlsession_get._find_the_object_in_f_locals_bfs(f_locals={'a': a, 'b': {}}, max_depth=3)
                assert obj is s


if __name__ == '__main__':
    unittest.main()
