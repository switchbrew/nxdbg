# Copyright 2017 plutoo
import struct
import AddressFormatter
from Types import *
from Adapter import *
from Utils import *

class AdapterStackTrace(Adapter):
    def __init__(self, usb, dbg_handle, tree):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.tree = tree

    def onDbgEvent(self, event):
        self.tree.clear()

        if event and event.thread_id != 0:
            try:
                ctx = self.usb.cmdGetThreadContext(self.dbg_handle, event.thread_id, 15)
            except SwitchError:
                return

            sp = struct.unpack('<Q', ctx[0xF8:0x100])[0]
            try:
                stack = self.usb.cmdReadMemory(self.dbg_handle, sp, 0x100)

                for i in range(len(stack)/8):
                    val = struct.unpack('<Q', stack[i*8 : i*8+8])[0]
                    addRow(self.tree, '0x%010x:   %s' % (sp + i*8, AddressFormatter.formatAddr(val, 0)))

            except SwitchError:
                addRow(self.tree, 'Access violation at sp=0x%010x' % sp)
