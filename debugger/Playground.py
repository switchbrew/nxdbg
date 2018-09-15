# Copyright 2017 plutoo
from Utils import *
from Lazy import *
from Types import *

BPK_INSTRUCTION=0xD4200000

class Playground:
    def __init__(self, usb, dbg_handle, parent):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.parent = parent

        self.log_file = open('nv_log.txt', 'w')

    def onDbgEvent(self, event):
        if not event:
            return

        if isinstance(event, ExceptionUndefinedInstruction):
            if event.per_exception == BPK_INSTRUCTION:
                addr = event.fault_reg
                '''
                if (addr & 0xFFFFF) == 0x14870:
                    self.log_file.write('Ioctl fd=0x%x cmd=0x%x\n' % (X[1], X[2]))
                    self.log_file.write(hexdump(read(r64(X[3]), (X[2] >> 16) & 0xFFF)))
                    self.parent.requestContinue()

                if (addr & 0xFFFFF) == 0x14854:
                    self.log_file.write('Open In\n')
                    self.log_file.write(hexdump(read(r64(X[1]), 0x20)))
                    self.saved_fd_out = X[2]

                if (addr & 0xFFFFF) == 0x14864:
                    self.log_file.write('Open Out fd=0x%x\n' % (r64(self.saved_fd_out) & 0xFFFFFFFF))
                    self.parent.requestContinue()
                '''

