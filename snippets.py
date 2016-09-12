#!/usr/bin/env
'''
Sharpening the saw.   Better python style tryouts.
'''

class InvalidPlasmaCurrentRange(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GetterSetterDemo:
    
    def __init__(self, ipla = 0):
        self.ipla = ipla

    @property
    def ipla(self):
        return self._ipla
    @ipla.setter
    def ipla(self, value):
        print("Setter called")
        if value < 0:
            raise InvalidPlasmaCurrentRange("Plasma current must be positive.")
        else:
            self._ipla = value


if __name__ == '__main__':
    jet = GetterSetterDemo(100)
    jet.ipla = -10
