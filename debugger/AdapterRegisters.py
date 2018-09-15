# Copyright 2017 plutoo
import struct
import AddressFormatter

from Adapter import *
from Utils import *
from Lazy import *

class AdapterRegisters(Adapter):
    def __init__(self, usb, dbg_handle, parent):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.parent = parent

        self.register_lineedits = [
            parent.lineX0,
            parent.lineX1,
            parent.lineX2,
            parent.lineX3,
            parent.lineX4,
            parent.lineX5,
            parent.lineX6,
            parent.lineX7,
            parent.lineX8,
            parent.lineX9,
            parent.lineX10,
            parent.lineX11,
            parent.lineX12,
            parent.lineX13,
            parent.lineX14,
            parent.lineX15,
            parent.lineX16,
            parent.lineX17,
            parent.lineX18,
            parent.lineX19,
            parent.lineX20,
            parent.lineX21,
            parent.lineX22,
            parent.lineX23,
            parent.lineX24,
            parent.lineX25,
            parent.lineX26,
            parent.lineX27,
            parent.lineX28,
            parent.lineX29,
            parent.lineX30,
            parent.lineSP,
            parent.linePC
        ]

    def onDbgEvent(self, event):
        if event and event.thread_id != 0:
            try:
                ctx = self.usb.cmdGetThreadContext(self.dbg_handle, event.thread_id, 15)

                for i in range(33):
                    self.register_lineedits[i].setText(AddressFormatter.formatAddr(struct.unpack('<Q', ctx[8*i : 8*i+8])[0], 0))
            except SwitchError:
                pass # can fail on ThreadAttach race condition
        else:
            for lineedit in self.register_lineedits:
                lineedit.setText('')
