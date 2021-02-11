import functools


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except:
                    print(f"FAILED TEST with arguments: {new_args[1]} \n\tin {new_args[0]}")
                    # traceback.print_exception(*sys.exc_info())
        return wrapper
    return decorator
