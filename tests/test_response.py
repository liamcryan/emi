import os
# import unittest

from requests import Response, PreparedRequest
from requests.adapters import HTTPAdapter
from requests_html import HTMLSession
from emi.api import MethodMock

htmlsession_get = MethodMock(method=HTMLSession.get)
HTMLSession.get = htmlsession_get.mock
MethodMock.directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures')


def get_http_response(*args, **get_kwargs):
    with HTMLSession() as s:
        r = s.get(*args, **get_kwargs)
        if not r.ok:
            raise Exception('unable to get url1: {}'.format(*args))
        return r


# class TestHTMLResponsesViaHTTP(unittest.TestCase):
#     url1 = 'https://google.com'
#
#     def delete(self):
#         for _ in os.listdir(htmlsession_get.directory):
#             if _ == '.gitkeep':
#                 continue
#             try:
#                 os.remove(os.path.join(htmlsession_get.directory, _))
#             except FileNotFoundError:
#                 pass
#
#     def setUp(self):
#         self.delete()
#
#     def tearDown(self):
#         self.delete()
#
#     @htmlsession_get.activate
#     def test_http_then_pickle_then_compare(self):
#         """ test that the http response you receive is the same as (close to) the pickled response"""
#         http_response1 = get_http_response(self.url1, verify=False)
#         pickled_response1 = htmlsession_get.get_method_response(1, self.url1, verify=False)
#         for attr in http_response1.__dict__:
#             if attr == '__getstate__':
#                 continue
#             elif attr == 'raw':
#                 assert pickled_response1.raw is None
#             elif attr == 'history':
#                 assert isinstance(pickled_response1.history[0], Response)
#             elif attr == 'request':
#                 assert isinstance(pickled_response1.request, PreparedRequest)
#             elif attr == 'session':
#                 assert isinstance(pickled_response1.session, HTMLSession)
#             elif attr == 'connection':
#                 assert isinstance(pickled_response1.connection, HTTPAdapter)
#             else:
#                 assert http_response1.__getattribute__(attr) == pickled_response1.__getattribute__(attr)
#
#     @htmlsession_get.activate
#     def test_same_two_http_then_two_different_pickles(self):
#         """ sometimes you expect different results from separate calls to the same function/args/kwargs.
#
#         test that multiple calls to the same function/args/kwargs provide separate pickled results.
#         """
#         http_response1 = get_http_response(self.url1, verify=False)
#         http_response2 = get_http_response(self.url1, verify=False)
#         pickled_response1 = htmlsession_get.get_method_response(1, self.url1, verify=False)
#         pickled_response2 = htmlsession_get.get_method_response(2, self.url1, verify=False)
#         assert http_response1.elapsed == pickled_response1.elapsed
#         assert http_response2.elapsed == pickled_response2.elapsed

@htmlsession_get.activate
def test_find_the_object():
    class A(object):
        def __init__(self, session):
            self.dummy1 = HTTPAdapter
            self.session = session
            self.dummy2 = Response

    class B(object):
        def __init__(self):
            self.dummy3 = PreparedRequest

    with HTMLSession() as s:
        a = A(session=s)
        b = B()
        # look through a and get the object (a.session)
        obj = htmlsession_get._find_the_object_in_f_locals(f_locals={'b': b, 'a': a})
        # obj is s...
        # need to make sure this is breadth first


    # need to test _find_the_object
    # provide more complex structure & make sure that _find_the_object is not too bad
    # it does a depth search first, so that's not good...


if __name__ == '__main__':
    test_find_the_object()
    # unittest.main()
