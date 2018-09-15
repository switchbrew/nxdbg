# Copyright 2017 plutoo
from Types import *
from Utils import *

lazySingleton = None
X = {}

def r64(addr):
    if not lazySingleton:
        return None
    return lazySingleton.r64(addr)

def read(addr, size):
    if not lazySingleton:
        return ''
    return lazySingleton.read(addr, size)

class Lazy:
    def __init__(self, usb, dbg_handle):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.invalidateRegisters()

        global lazySingleton
        lazySingleton = self

    def invalidateRegisters(self):
        global X
        for i in range(31):
            X[i] = None
        global SP
        SP = None
        global PC
        PC = None

    def onDbgEvent(self, event):
        if not event or event.thread_id == 0:
            self.invalidateRegisters()
            return

        try:
            ctx = self.usb.cmdGetThreadContext(self.dbg_handle, event.thread_id, 15)
        except SwitchError:
            self.invalidateRegisters()
            return

        global X
        for i in range(31):
            X[i] = struct.unpack('<Q', ctx[8*i : 8*i+8])[0]
        i = 31 # SP
        X[i] = struct.unpack('<Q', ctx[8*i : 8*i+8])[0]
        i = 32 # PC
        X[i] = struct.unpack('<Q', ctx[8*i : 8*i+8])[0]

    def r64(self, addr):
        buf = ''
        try:
            buf = self.usb.cmdReadMemory(self.dbg_handle, addr, 8)
        except SwitchError:
            return None
        return struct.unpack('<Q', buf)[0]

    def read(self, addr, size):
        buf = ''
        try:
            buf = self.usb.cmdReadMemory(self.dbg_handle, addr, size)
        except SwitchError:
            return ''
        return buf
