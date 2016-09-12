#REF http://stackoverflow.com/questions/4689984/implementing-a-callback-in-python-passing-a-callable-reference-to-the-current
class Event(object):
    pass

class Observable(object):
    def __init__(self):
        self.callbacks = []
    def subscribe(self, callback):
        self.callbacks.append(callback)
    def fire(self, **attrs):
        e = Event()
        e.source = self
        for k, v in attrs.iteritems():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)

# Ref http://curiosityhealsthecat.blogspot.co.uk/2013/07/using-python-decorators-for-registering_8614.html

# Decorators almost exactly explain part of my idea.

# Build the executable concept with partial ?   See itertools

def add(arg, *args):
    constant = args[0]
    return arg + constant

# Work out the usage, then work backwards ???
