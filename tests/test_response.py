import os
import unittest
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


class TestHTMLResponses(unittest.TestCase):
    url1 = 'https://google.com'
    url2 = 'https://yahoo.com'

    @htmlsession_get.activate
    def test_get_saved_method_response_url1_and_url2(self):
        """ Opens up the pickle file in the fixture folder and retrieves the
        HTTP.get method matching the args & kwargs provided.  The pickle file
        contains the actual response so that tests will not need HTTP calls. """

        http_response1 = get_http_response(self.url1, verify=False)
        data = {'_content': http_response1._content,
                '_content_consumed': http_response1._content_consumed,
                '_html': http_response1._html,
                '_next': http_response1._next,
                'apparent_encoding': http_response1.apparent_encoding,
                'connection': http_response1.connection,
                'content': http_response1.content,
                'cookies': http_response1.cookies,
                'elapsed': http_response1.elapsed,
                'encoding': http_response1.encoding,
                'headers': http_response1.headers,
                'history': http_response1.history,
                'html': http_response1.html,
                'is_permanent_redirect': http_response1.is_permanent_redirect,
                'is_redirect': http_response1.is_redirect,
                'links': http_response1.links,
                'next': http_response1.next,
                'ok': http_response1.ok,
                'raw': http_response1.raw,
                'reason': http_response1.reason,
                'request': http_response1.request,
                'session': http_response1.session,
                'status_code': http_response1.status_code,
                'text': http_response1.text,
                'url': http_response1.url
                }
        # http_response2 = get_http_response(self.url2, verify=False)

        pickled_response1 = htmlsession_get.get_method_response(self.url1, verify=False)
        for attr in data:
            assert hasattr(pickled_response1, attr)

        # test asserts that the pickled response has all of the attributes but nothing about the values :(

if __name__ == '__main__':
    unittest.main()
