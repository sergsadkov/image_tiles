# Auxiliary files used for testing

from datetime import datetime


def functionWorkTime(func):
    def wrapped(*args, **kwargs):
        t = datetime.now()
        res = func(*args, **kwargs)
        print(func.__qualname__, datetime.now() - t)
        return res
    return wrapped