import os
import fnmatch
import unittest

from requests_html import HTMLSession
from emi.api import MethodMock

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


def set_up(url):
    htmlsession_get.activate(set_up)
    get_http_response(url)
    htmlsession_get.deactivate()


def go_1(url):
    htmlsession_get.activate(go_1)
    get_http_response(url)
    htmlsession_get.deactivate()


def go_2(url):
    htmlsession_get.activate(go_2)
    get_http_response(url)
    htmlsession_get.deactivate()


def go_3(url):
    htmlsession_get.activate(go_3)
    get_http_response(url)
    htmlsession_get.deactivate()


class TestFixture(unittest.TestCase):
    url = 'https://google.com'

    @staticmethod
    def clean_up():
        for file in os.listdir(MethodMock.directory):
            if file == '.gitkeep':
                continue
            os.remove(os.path.join(MethodMock.directory, file))

    @classmethod
    def setUpClass(cls):
        set_up(cls.url)
        go_1(cls.url)
        set_up(cls.url)
        go_2(cls.url)
        set_up(cls.url)
        go_3(cls.url)

    @classmethod
    def tearDownClass(cls):
        cls.clean_up()

    def test_file_qty_correct(self):
        patterns = {'*set_up*': False, '*set_up.1*': False, '*set_up.2*': False, '*go_1*': False, '*go_2*': False,
                    '*go_3*': False}

        for file in os.listdir(MethodMock.directory):
            for pattern in patterns:
                if fnmatch.fnmatch(file, pattern):
                    patterns[pattern] = True
                    continue

        for pattern in patterns:
            assert patterns[pattern]


if __name__ == '__main__':
    unittest.main()

