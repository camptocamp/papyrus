# Workaround AttributeError: module 'collections' has no attribute 'Callable'
# Nose is abandonned since 2015. A proper solution would be to switch to pytest
import collections

if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable
