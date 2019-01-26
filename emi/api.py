import functools
import inspect
import os
import pickle
import types
from typing import Dict, Any, Union, Generator, Optional

__all__ = ('MethodMock', 'MaxDepthExceeded')


class MaxDepthExceeded(Exception):
    pass


def __getstate__(self) -> Dict:
    """ Used by pickle when pickle.dump(s) is called.

    Check to see if the attribute is pickle-able.  If not, then essentially disregard it.

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
            '{}.{}'.format(func.__module__, func.__qualname__): {'method_count': 0}})

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = func(*args, **kwargs)
            return r

        return wrapper

    def _get_active_test(self):
        for stack in inspect.stack():
            for test in self.activated_tests:
                if test.split('.')[-1] == stack.function:
                    return test

    def _find_the_object_in_f_locals_bfs(self, f_locals, max_depth=5):
        """ Find the correct object in f_locals.

        The object we want looks like: obj.(self.method.__name__) == self.mock

        The structure could be:
            obj.(self.method.__name__)
            c.(self.method.__name__)
            ...
            A.b.c.obj.(self.method.__name__)

        Since we don't know the structure of exactly where the obj is called, we do a breadth
        first search to find it.  BFS in this case is what I want, because we don't travel
        down one branch before visiting other branches.  I am thinking that most objects
        will not be heavily nested, but may have some nesting, so max_depth is set to 5.

        Also, if the object is nested, it must be contained in 'container.__dict__'.  This means
        only instance attributes wil be found.  Will not find class attributes, however could if the
        below used 'dir(container)' instead.

        :param f_locals: f_locals is frame locals.  Or a dict like {'a': a_obj, 'b': b_obj, ...}
        :return: the object
        :raise: MaxDepthExceeded
        """

        class NextFLocals(object):
            def __init__(self):
                self.f_locals = {}

            def update(self, data: Dict):
                try:
                    self.f_locals.update(data.__dict__)
                except AttributeError:
                    pass

        next_f_locals = NextFLocals()
        depth = 0

        while depth <= max_depth:
            for loc in f_locals:
                _object = f_locals[loc]
                try:
                    if getattr(_object, self.method.__name__) == self.mock:
                        return _object
                    else:
                        next_f_locals.update(_object)
                except AttributeError:
                    next_f_locals.update(_object)
            else:
                depth += 1
                f_locals = next_f_locals.f_locals
                next_f_locals.f_locals = {}

        raise MaxDepthExceeded('Could not find the object with depth of {} exceeded'.format(max_depth))

    def mock(self, *args, **kwargs) -> Any:
        """  Replace a method with a mock instead.

        Behavior is:
            mock will only run if activated with a decorator
            actual method will run if there is no pickle file

        :return: the results of the pickle file or result of the actual method
        """

        self.activated_test = self._get_active_test()
        mock_obj = self._find_the_object_in_f_locals_bfs(f_locals=inspect.currentframe().f_back.f_locals)

        if self.activated_test:
            self.activated_tests[self.activated_test]['method_count'] += 1  # add one to the function count
            method_count = self.activated_tests[self.activated_test]['method_count']
            pickled_results = self.get_method_response(method_count)
            if pickled_results:
                return pickled_results

            r = self.method(mock_obj, *args, **kwargs)
            self.save_method_response(r, method_count)
            return r

        return self.method(mock_obj, *args, **kwargs)

    def _open_pickle(self) -> Optional[Generator]:
        """ loading multiple objects contained in a list at once has unexpected effects
        where some items in the list do not load correctly.  this will load each pickle.  make sure to
        close this file by iterating through all items even if you have the one you are looking for """
        try:
            with open(os.path.join(self.directory, self.filename()), 'rb') as f:
                while True:
                    try:
                        yield pickle.load(f)
                    except EOFError:
                        break
        except FileNotFoundError:
            pass

    def get_method_response(self, method_count: int) -> Union[Any, None]:
        """ Get the method's actual response from the pickled file.

        :method_count: identify the count of the method (how many times it has been called)
        :return: the method's actual response or None if FileNotFound
        """
        data = list(self._open_pickle())  # iterate through everything so the file closes
        for _ in data:
            if self._id(method_count) in _:
                return _[self._id(method_count)]

    def save_method_response(self, _method_response, method_count: int):
        """ Pickle the method's actual response.

        :param _method_response: the method's actual response.  Only pickle-able attributes will be pickled.
        :param method_count: identify the count of the method (how many times it has been called)
        :return: None
        """
        _method_response.__getstate__ = types.MethodType(__getstate__, _method_response)

        with open(os.path.join(self.directory, self.filename()), 'ab') as f:
            pickle.dump({self._id(method_count): _method_response}, f)

    def _id(self, method_count: int):
        """ an id that uniquely identifies the called mocked method (test, method, args, kwargs, count)"""
        activated_test = self.activated_test + '.'
        method = self.method.__qualname__ + '.'
        return activated_test + str(method_count)

    def filename(self):
        """ a filename that identifies the test and mock method """
        f_name = '{}-{}.pickle'.format(self.activated_test, self.method.__qualname__)
        return f_name
