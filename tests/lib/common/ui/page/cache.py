from functools import wraps


def cache(func):
    saved = {}

    @wraps(func)
    def new_func(*args):
        if args in saved:
            return saved[args]
        result = func(*args)
        saved[args] = result
        return result
    return new_func
