#!/usr/bin/env python

'''
Support classes for manipulating plugin functions and heuristics for piwall image processing.

Of more general use.
'''

import pdb

class Plugin:
    def __init__(self, plugin, *args, **kwargs):
        self.plugin = plugin
        self.args = args
        self.kwargs = kwargs
    def call(self, signature):
        pdb.set_trace()
        return self.plugin(signature, self.args, self.kwargs)
    def __repr__(self):
        return '''Plugin wraps function %s to be called with args %s and kwargs %s''' % (self.plugin.__name__, self.args, self.kwargs)

class Heuristics:
    '''Container for a set of plugins with hints/options to be tuned for a given image/image set.'''
    def __init__(self):
        self.plugins = OrderedDict()
    def register_plugin(self, plugin, *args, **kwargs):
        self.plugins[plugin.__name__] = Plugin(plugin, args, kwargs)
    def __repr__(self):
        s = []
        return '\n'.join(s)

class WallHint:
    def __init__(self, *args):
        self.args = args
    def call(self, img, cnts):
        return cnts
    def __repr__(self):
        pass

class FilterLargeAreas(WallHint):
    pass
    #self.__super__.__init__()
    #foo
    #pass

    
# Unit Tests


# Set of plugins for manipulating lists of integers

def add(ilist, *args, **kwargs):
    pdb.set_trace()
    return [i+args[0] for i in ilist]

def scale(ilist, *args, **kwargs):
    return [i*args[0] for i in list]

def lookup(ilist, *args, **kwargs):
    '''Substitute integers for symbols if found in kwargs'''
    lookup = lambda i: kwargs[i] if i in kwargs else i
    return map(lookup, ilist)

def ut_plugins():
    fib_list = [1,1,2,3,5,8,13,21,34,55]
    fib_faves = {13 : 'triskaideka', 55 : 'nice symmetry'}
    add_five = Plugin(add, 5, a=10)
    times_ten = Plugin(scale, 1, b=10)
    comment = Plugin(lookup, fib_faves)
    fib_list_plus_five = add_five.call(fib_list)
    printf(fib_list_plus_five)
    fib_list_times_ten = times_ten.call(fib_list)
    printf(fib_list_times_ten)
    fib_list_faves_filter = comment.call(fib_list)
    printf(fib_list_faves_filter)

if __name__ == '__main__':
    ut_plugins()
