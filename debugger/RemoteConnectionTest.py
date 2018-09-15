# Copyright 2018 plutoo
from RemoteConnection import *

DUMMY_ADDR_SPACE = [
    (       0,         0x100000, 0,  0), # Unmapped
    (0x100000,           0x2000, 5,  3), # CodeStatic
    (0x102000, (1<<48)-0x102000, 0,  0), # Unmapped
    (   1<<48,            1<<64, 0, 16),
]

class RemoteConnectionTest(RemoteConnection):
    def __init__(self):
        RemoteConnection.__init__(self)

    def read(self, size):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def cmdDetachProcess(self, handle): # Cmd2
        pass

    def cmdQueryMemory(self, handle, addr): # Cmd3
        for r in DUMMY_ADDR_SPACE:
            if addr >= r[0] and addr < (r[0] + r[1]):
                return {'addr': r[0], 'size': r[1], 'perm': r[2], 'type': r[3]}
        raise
