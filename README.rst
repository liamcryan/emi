-------------------
(e)asy (m)ock(i)ing
-------------------

emi was inspired by vcrpy.  Instead of listening for http calls and saving them, you might want to listen
to something more generic.  How about we listen to anything and save the response as a pickled
object?  Caveat: if your response value is pickle-able or has pickle-able attributes, then yay, otherwise,
this isn't what you're looking for.  Also, everything is pickled, so it's not super duper fast.

How this works is the first run of your test will run normally, with the exception that the response
will be saved.  In the next runs, the saved response will be used instead.  Here's an example of
usage::

    from requests_html import HTMLSession
    import emi

    # create a MethodMock instance
    htmlsession_get = emi.MethodMock(method=HTMLSession.get)

    # set the instance's mock method to the method you want to mock (want to mock HTMLSession.get)
    HTMLSession.get = htmlsession_get.mock

    def my_boolean_method(url):
        with HTMLSession() as s:
            r = s.get(url)  #  <-- oooohhhh, this is actually the mocked method, not plain old HTMLSession.get!
            if r.ok:
                return True

    @htmlsession_get.activate  # htmlsession_get will activate and be used instead of HTMLSession.get
    def test_my_boolean_method():
        assert my_boolean_method(url='https://google.com') is True

    if __name__ == '__main__':
        test_my_boolean_method()  # run this for the first time and s.get will reach out to the internet and save the response
        test_my_boolean_method()  # run this again and s.get will use the saved response!


Next steps
__________

This could be re-implemented using unittest.MagicMock with a side effect of saving or retrieving a the pickle.  This
will be simpler I think.  Also, there is quite a bit of lines to get set up...I want to look into reducing this.
