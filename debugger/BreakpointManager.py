# Copyright 2017 plutoo
import struct
import AddressFormatter
from Types import *
from Utils import *

BPK_INSTRUCTION=0xD4200000

class SwBreakpoint:
    def __init__(self, usb, dbg_handle, addr):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.addr = addr

        old_insn = self.usb.cmdReadMemory(self.dbg_handle, addr, 4)
        self.old_insn = struct.unpack('<I', old_insn)[0]

        self.usb.cmdWriteMemory32(self.dbg_handle, addr, BPK_INSTRUCTION)

    def setThreadId(self, thread_id):
        self.thread_id = thread_id

    def insert(self):
        self.usb.cmdWriteMemory32(self.dbg_handle, self.addr, BPK_INSTRUCTION)

    def remove(self):
        self.usb.cmdWriteMemory32(self.dbg_handle, self.addr, self.old_insn)

    def wakeupThread(self):
        self.remove()
        self.usb.cmdContinueDbgEvent(self.dbg_handle, 2|1, self.thread_id)
        self.insert()

class BreakpointManager:
    def __init__(self, usb, dbg_handle, tree):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.tree = tree

        self.bp = {}
        self.bp_refcnt = {}
        self.active_bp = None

    def onDbgEvent(self, event):
        if requiresContinue(event):
            for bp in self.bp.values():
                bp.remove()

        if isinstance(event, ExceptionUndefinedInstruction):
            if event.per_exception == BPK_INSTRUCTION:
                addr = event.fault_reg
                self.bp[addr].setThreadId(event.thread_id)
                self.active_bp = self.bp[addr]

    def addSwBreakpoint(self, addr):
        if addr in self.bp_refcnt:
            self.bp_refcnt[addr] += 1
        else:
            self.bp[addr] = SwBreakpoint(self.usb, self.dbg_handle, addr)
            self.bp_refcnt[addr] = 1

        self.refreshUi()

    def delSwBreakpoint(self, addr):
        self.bp_refcnt[addr] -= 1

        if self.bp_refcnt[addr] == 0:
            self.bp[addr].remove()

            if self.active_bp == self.bp[addr]:
                self.active_bp = None

            del self.bp_refcnt[addr]
            del self.bp[addr]

        self.refreshUi()

    def continueDbgEvent(self):
        for bp in self.bp.values():
            bp.insert()

        if self.active_bp:
            self.active_bp.wakeupThread()

    def cleanup(self):
        for bp in self.bp.values():
            bp.remove()

        self.bp = {}
        self.bp_refcnt = {}

    def refreshUi(self):
        self.tree.clear()

        for bp in self.bp:
            addRow(self.tree, AddressFormatter.formatAddr(bp), 'SwBreakpoint')
