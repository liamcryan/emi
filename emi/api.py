import functools
import inspect
import os
import pickle
import types
from typing import Dict, Any, Union

__all__ = ['MethodMock', '__getstate__']


def __getstate__(self) -> Dict:
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
        self.activated_test = None

    def mock(self, *args, **kwargs) -> Any:
        """  Replace a method with a mock instead.

        Behavior is:
            mock will only run if activated with a decorator
            actual method will run if there is no pickle file

        :param args: args used to identify the method to be mocked
        :param kwargs: kwargs used to identify the method to be mocked
        :return: the results of the pickle file or result of the actual method
        """
        if self.activated_test:  # if method applies to a test
            pickled_results = self.get_method_response(*args, **kwargs)
            if pickled_results:
                return pickled_results

        f_locals = inspect.currentframe().f_back.f_locals

        obj = None
        for loc in f_locals:
            try:
                mock_method = getattr(f_locals[loc], self.method.__name__)
                if mock_method.__name__ == self.mock.__name__:
                    obj = f_locals[loc]
                    break
            except AttributeError:
                continue

        if not obj:
            raise Exception('could not access the correct object')

        r = self.method(obj, *args, **kwargs)
        self.save_method_response(r, *args, **kwargs)

        return r

    def _open_pickle(self):
        try:
            with open(os.path.join(self.directory, self.filename()), 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            pass

    def get_method_response(self, *args, **kwargs) -> Union[Any, None]:
        """ Get the method's actual response from the pickled file.

        :return: the method's actual response or None if FileNotFound
        """
        pickled_data = self._open_pickle()
        if pickled_data:
            return pickled_data.get(self._id(*args, **kwargs), None)

    def save_method_response(self, data, *args, **kwargs):
        """ Pickle the method's actual response.

        :param data: the method's actual response.  Only pickle-able attributes will be pickled.  Any
                    attributes which are not pickle-able will return the TypeError explaining that the attribute
                    could not be pickled.
        :param args: args to the method being mocked
        :param kwargs: kwargs to the method being mocked
        :return: None
        """
        data.__getstate__ = types.MethodType(__getstate__, data)

        pickled_data = self._open_pickle()  # will be {test.method.args.kwargs: '', ...}
        if not pickled_data:
            pickled_data = {}

        with open(os.path.join(self.directory, self.filename()), 'wb') as f:
            pickled_data.update({self._id(*args, **kwargs): data})
            pickle.dump(pickled_data, f)

    def _id(self, *args, **kwargs):
        """ an id that uniquely identifies the called mocked method (test, method, args, kwargs)"""
        activated_test = self.activated_test + '.'
        method = self.method.__qualname__ + '.'
        _args = str(tuple(sorted(args))) + '.'
        _kwargs = '{'
        for _ in sorted(kwargs):
            _kwargs += str(_) + ':' + str(kwargs[_])
        _kwargs += '}'

        return activated_test + method + _args + _kwargs

    def filename(self):
        """ a filename that identifies the test and mock method """
        return '{}-{}.pickle'.format(self.activated_test, self.method.__qualname__)  # ':' cannot be in filename

    def activate(self, func):
        self.activated_test = func.__qualname__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = func(*args, **kwargs)
            return r

        return wrapper

    def delete(self):
        try:
            os.remove(os.path.join(self.directory, self.filename()))
        except FileNotFoundError:
            pass
