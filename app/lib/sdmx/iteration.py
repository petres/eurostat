import sys

if sys.version_info[0] == 2:
    import __builtin__
    import itertools

    class EagerIteration(object):
        map = __builtin__.map

    class LazyIteration(object):
        map = itertools.imap

else:
    import builtins
    
    class EagerIteration(object):
        @staticmethod
        def map(*args, **kwargs):
            return list(map(*args, **kwargs))

    class LazyIteration(object):
        map = builtins.map
