# Copyright 2017 plutoo
from PyQt4 import QtGui
import types

import ArmDisassembler
import AddressFormatter

from Types import *
from Lazy import *
from Utils import *


def outGrey(textOutput, text):
    if text.endswith('\n'): text=text[:-1]
    textOutput.setTextColor(QtGui.QColor(0x77, 0x77, 0x77))
    textOutput.append(text)

def outRed(textOutput, text):
    if text.endswith('\n'): text=text[:-1]
    textOutput.setTextColor(QtGui.QColor(0xFF, 0x33, 0x33))
    textOutput.append(text)

def outWhite(textOutput, text):
    if text.endswith('\n'): text=text[:-1]
    textOutput.setTextColor(QtGui.QColor(0xFF, 0xFF, 0xFF))
    textOutput.append(text)

class DisassemblyString:
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return '\n' + self.s

class ExpressionEvaluator:
    def __init__(self, usb, dbg_handle, parent):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.parent = parent

        self.glob = {
            'u': self.cmdDisasm,
            'g': self.cmdContinue,
            'q': self.cmdQuit,
            'bp': self.cmdAddBreakpoint,
            'bc': self.cmdDelBreakpoint,
            'b': self.cmdBreakProcess,
            'd': self.cmdHexdump,
            'df': self.cmdDumpFile,
            'ed': self.cmdWrite32,
            'f': self.cmdFind
        }

    def superEvilEval(self, param):
        nsos = AddressFormatter.getNsos()
        for n in nsos:
            self.glob[n] = nsos[n]['addr']

        for i in range(31):
            if i in X:
                self.glob['x%d'%i] = X[i]

        if 31 in X:
            self.glob['sp'] = X[31]
        if 32 in X:
            self.glob['pc'] = X[32]

        self.glob['poi'] = r64
        self.glob['r64'] = r64

        param = eval(param, self.glob, self.glob)
        return param

    def cmdHexdump(self, addr, size=0x100):
        buf = self.usb.cmdReadMemory(self.dbg_handle, addr, size)
        return DisassemblyString(hexdump(buf, 16, addr))

    def cmdDumpFile(self, file_name, addr, size=0x100):
        pos = 0
        f = open(file_name, 'wb')
        rem = size
        while pos < size:
            chunk_size = min(rem, 0x800)

            buf = self.usb.cmdReadMemory(self.dbg_handle, addr + pos, chunk_size)
            f.write(buf)

            pos += chunk_size
            rem -= chunk_size

        f.close()

    def cmdDisasm(self, addr, size=4):
        size = 4*size

        buf = self.usb.cmdReadMemory(self.dbg_handle, addr, size)
        return DisassemblyString(ArmDisassembler.Dis(addr, buf))

    def cmdFind(self, pattern, find_max=None):
        pattern = pattern.decode('hex')

        found_num = 0
        addr = 0

        result = ''

        while not find_max == None or found_num < find_max:
            outWhite(out, 'Searching at 0x%x..' % addr)
            ret = self.usb.cmdQueryMemory(self.dbg_handle, addr)

            if ret['type'] == 0x10:
                break

            if ret['perm'] & 1:
                for off in range(0, ret['size'], 0x1000):
                    try:
                        buf = self.usb.cmdReadMemory(self.dbg_handle, addr+off, 0x1000)
                    except:
                        #outRed(out, 'Failed to read 0x%x..' % (addr+off))
                        buf = ''

                    if pattern in buf:
                        result += 'Found at address: 0x%x\n' % (addr+off+buf.find(pattern))
                        found_num+=1
                        break

                addr = ret['addr'] + ret['size']

        return result

    def cmdWrite32(self, addr, val):
        self.usb.cmdWriteMemory32(self.dbg_handle, addr, val)

    def cmdContinue(self):
        self.parent.continueDbgEvent()

    def cmdQuit(self):
        self.parent.close()

    def cmdAddBreakpoint(self, addr):
        self.parent.bp_manager.addSwBreakpoint(addr)

    def cmdDelBreakpoint(self, addr):
        self.parent.bp_manager.delSwBreakpoint(addr)

    def cmdBreakProcess(self):
        if not self.parent.active_event:
            self.usb.cmdBreakProcess(self.dbg_handle)

    def execute(self, textOutput, lineCmd):
        cmd = str(lineCmd.text())

        if cmd.strip() == '':
            return

        outWhite(textOutput, '>>> ' + cmd)

        try:
            value = self.superEvilEval(cmd)
            if type(value) == types.MethodType:
                try:
                    value = value()
                except:
                    pass
            value = '[%s] %s' % (type(value), repr(value))
            outWhite(textOutput, value)
        except Exception, e:
            outRed(textOutput, repr(e))
