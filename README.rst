-------------------
(e)asy (m)ock(i)ing
-------------------

emi is a library that mocks an instance of a method you specify.  It will record the result of the
instance method the first time it is run and use this result on subsequent runs.  Here's an example::

    from requests_html import HTMLSession
    import emi

    easy_mock_method = emi.MethodMock(method=HTMLSession.get)
    HTMLSession.get = easy_mock_method.mock

    # imports for the test function must be after the easy mock definitions
    from my_module import my_boolean_method

    @easy_mock_method.activate  # easy_mock_method will activate and be used instead of HTMLSession.get
    def test_my_boolean_method():
        assert my_boolean_method(url='https://google.com') is True


Plans
_____

There seem to be a few roadblocks while creating this...

- monkey patching after importing instead of before?
- pickling is a little tricky.  for complex objects like a requests.Response, it seems like a lot of __getstate__
get called.  what is the order?  my example works, but I feel like I am missing something?
- pickle security?
