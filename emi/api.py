import functools
import inspect
import os
import pickle
import types
from typing import Dict, Any, Union, Generator, Optional


def __getstate__(self) -> Dict:
    """ Used by pickle when pickle.dump(s) is called.

    Check to see if the attribute is pickle-able.  If not, then
    essentially disregard it.

    :return: a dictionary of pickle-able objects
    """
    state = {}
    for attr in self.__dict__:
        if attr in ('__getstate__',):
            continue
        try:
            pickle.dumps(self.__dict__[attr])
            state.update({attr: self.__dict__[attr]})
        except TypeError:
            state.update({attr: None})

    return state


class MethodMock(object):
    directory = ''

    def __init__(self, method):
        self.method = method
        self.activated_tests = {}
        self.activated_test = None  # this changes each time mock gets called

    def activate(self, func):
        """ A function that decorates the test.

        Activate the mock for the specified test and initialize the counts to zero.

        :param func: this is the function being decorated.
        :return the same function.
        """
        self.activated_tests.update({
            '{}.{}'.format(func.__module__, func.__qualname__): {'mock': 0, 'get': 0}})

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = func(*args, **kwargs)
            return r

        return wrapper

    def _get_active_test(self):
        for stack in inspect.stack():
            func_name = stack.function
            for test in self.activated_tests:
                if test.split('.')[-1] == func_name:
                    return test

    def _find_the_object_in_f_locals(self, f_locals):
        # is f_loc1.1? f_loc2.1? f_loc3.1?
        # how about f_loc1.2? f_loc2.2? f_loc3.2?
        # ...
        for loc in f_locals:
            try:
                obj = self._find_the_object(_object=f_locals[loc])
                if obj:
                    break
                else:
                    continue
            except RecursionError:
                continue
        else:
            raise Exception('could not find the correct object')

    def _find_the_object(self, _object):
        """ Find the correct object.  Look through all of the attrs object's __dict__ too (depth first).

        If the object under consideration has a _method, that's good.  Then
        check if it's the same as _mock.

        :param _object: the object under consideration
        :return: the object if it is the correct one, or None
        """
        try:
            if getattr(_object, self.method.__name__) == self.mock:
                return _object
            else:
                pass
        except AttributeError:
            pass

        try:
            _attrs = _object.__dict__
        except AttributeError:
            return None

        for _attr in _attrs:
            try:
                return self._find_the_object(_object=_object.__dict__[_attr])
            except RecursionError:
                continue

    def mock(self, *args, **kwargs) -> Any:
        """  Replace a method with a mock instead.

        Behavior is:
            mock will only run if activated with a decorator
            actual method will run if there is no pickle file

        :param args: args used to identify the method to be mocked
        :param kwargs: kwargs used to identify the method to be mocked
        :return: the results of the pickle file or result of the actual method
        """

        self.activated_test = self._get_active_test()

        if self.activated_test:
            self.activated_tests[self.activated_test]['mock'] += 1  # add one to the function count
            method_count = self.activated_tests[self.activated_test]['mock']
            pickled_results = self.get_method_response(method_count, *args, **kwargs)
            if pickled_results:
                return pickled_results

        last_frame = inspect.currentframe().f_back
        f_locals = last_frame.f_locals
        obj = self._find_the_object_in_f_locals(f_locals=f_locals)

        r = self.method(obj, *args, **kwargs)

        if self.activated_test:
            self.save_method_response(r, method_count, *args, **kwargs)

        return r

    def _open_pickle(self, *args, **kwargs) -> Optional[Generator]:
        """ loading multiple objects contained in a list at once has unexpected effects
        where some items in the list do not load correctly.  this will load each pickle.  make sure to
        close this file by iterating through all items even if you have the one you are looking for """
        try:
            with open(os.path.join(self.directory, self.filename(*args, **kwargs)), 'rb') as f:
                while True:
                    try:
                        yield pickle.load(f)
                    except EOFError:
                        break
        except FileNotFoundError:
            pass

    def get_method_response(self, method_count, *args, **kwargs) -> Union[Any, None]:
        """ Get the method's actual response from the pickled file.

        :return: the method's actual response or None if FileNotFound
        """
        data = list(self._open_pickle(*args, **kwargs))  # iterate through everything so the file closes
        for _ in data:
            if self._id(method_count, *args, **kwargs) in _:
                return _[self._id(method_count, *args, **kwargs)]

    def save_method_response(self, _method_response, method_count, *args, **kwargs):
        """ Pickle the method's actual response.

        :param _method_response: the method's actual response.  Only pickle-able attributes will be pickled.
        :param method_count: identify the count of the method (how many times it has been called)
        :param args: args to the method being mocked
        :param kwargs: kwargs to the method being mocked
        :return: None
        """
        _method_response.__getstate__ = types.MethodType(__getstate__, _method_response)

        with open(os.path.join(self.directory, self.filename(*args, **kwargs)), 'ab') as f:
            pickle.dump({self._id(method_count, *args, **kwargs): _method_response}, f)

    def _id(self, method_count, *args, **kwargs):
        """ an id that uniquely identifies the called mocked method (test, method, args, kwargs, count)"""
        activated_test = self.activated_test + '.'
        method = self.method.__qualname__ + '.'
        _args = str(tuple(sorted(args))) + '.'
        _kwargs = '{'
        for _ in sorted(kwargs):
            _kwargs += str(_) + ':' + str(kwargs[_])
        _kwargs += '}.'

        return activated_test + method + _args + _kwargs + str(method_count)

    def filename(self, *args, **kwargs):
        """ a filename that identifies the test and mock method """
        f_name = '{}-{}.pickle'.format(self.activated_test, self.method.__qualname__)
        return f_name
