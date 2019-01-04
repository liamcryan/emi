-------------------
(e)asy (m)ock(i)ing
-------------------

emi is a library that mocks an instance of a method you specify.  It will record the result of the
instance method the first time it is run and use this result on subsequent runs.  Here's an example::

    from requests_html import HTMLSession
    import emi

    htmlsession_get = emi.MethodMock(method=HTMLSession.get)
    HTMLSession.get = htmlsession_get.mock

    def my_boolean_method(url):
        with HTMLSession() as s:
            r = s.get(url)  #  <-- oooohhhh, this is actually the mocked method!
            if r.ok:
                return True

    @htmlsession_get.activate  # easy_mock_method will activate and be used instead of HTMLSession.get
    def test_my_boolean_method():
        assert my_boolean_method(url='https://google.com') is True

    if __name__ == '__main__':
        test_my_boolean_method()  # run this for the first time and s.get will reach out to the internet
        test_my_boolean_method()  # run this again and s.get won't! it saves your response.

Plans
_____

There seem to be a few roadblocks while creating this...

- monkey patching after importing instead of before?
- pickling is a little tricky.  for complex objects like a requests.Response, it seems like a lot of __getstate__
get called.  what is the order?  my example works, but I feel like I am missing something?
- pickle security?
