# Copyright 2017 plutoo
from PyQt4 import QtGui
import ArmDisassembler
from UsbConnection import *
from Lazy import *
from Utils import *

def outGrey(textOutput, text):
    textOutput.setTextColor(QtGui.QColor(0x77, 0x77, 0x77))
    textOutput.append(text)

def outRed(textOutput, text):
    textOutput.setTextColor(QtGui.QColor(0xFF, 0x33, 0x33))
    textOutput.append(text)

def outBlack(textOutput, text):
    textOutput.setTextColor(QtGui.QColor(0, 0, 0))
    textOutput.append(text)

class ExpressionEvaluator:
    def __init__(self, usb, dbg_handle, parent):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.parent = parent

        self.cmd_table = {
            'u': self.cmdDisasm,
            'g': self.cmdContinue,
            'q': self.cmdQuit,
            'bp': self.cmdAddBreakpoint,
            'bc': self.cmdDelBreakpoint,
            'b': self.cmdBreakProcess,
            'd': self.cmdHexdump
        }

    def superEvilEval(self, param):
        try:
            glob = {}
            for i in range(31):
                glob['x%d'%i] = X[i]

            glob['sp'] = X[31]
            glob['pc'] = X[32]
            glob['poi'] = r64
            glob['r64'] = r64

            param = eval(param, glob, {})
            return param
        except:
            raise Exception('Bad syntax')

    def superEvilEvalDoubleArg(self, param, default=None):
        param = self.superEvilEval(param)

        if default is None:
            if type(param) != tuple or len(param) != 2:
                raise Exception('This command requires at two args')
            return param

        else:
            if type(param) == int:
                return (param, default)
            if type(param) == tuple and len(param) != 2:
                raise Exception('This command requires one or two args')

            return param

    def cmdHexdump(self, out, param):
        addr, size = self.superEvilEvalDoubleArg(param, 0x100)

        buf = ''
        try:
            buf = self.usb.cmdReadMemory(self.dbg_handle, addr, size)
        except SwitchError:
            outRed(out, 'Failed to read')
            return

        outBlack(out, hexdump(buf, 16, addr))

    def cmdDisasm(self, out, param):
        addr, size = self.superEvilEvalDoubleArg(param, 4)
        size = 4*size

        buf = ''
        try:
            buf = self.usb.cmdReadMemory(self.dbg_handle, addr, size)
        except SwitchError:
            outRed(out, 'Failed to read')
            return

        outBlack(out, ArmDisassembler.Dis(addr, buf))

    def cmdContinue(self, out, param):
        self.parent.continueDbgEvent()

    def cmdQuit(self, out, param):
        self.parent.close()

    def cmdAddBreakpoint(self, out, param):
        addr = self.superEvilEval(param)
        self.parent.bp_manager.addSwBreakpoint(addr)

    def cmdDelBreakpoint(self, out, param):
        addr = self.superEvilEval(param)
        self.parent.bp_manager.delSwBreakpoint(addr)

    def cmdBreakProcess(self, out, param):
        if not self.parent.active_event:
            self.usb.cmdBreakProcess(self.dbg_handle)

    def execute(self, textOutput, lineCmd):
        cmd = str(lineCmd.text()).strip()

        p = cmd.split()
        if len(p) == 0:
            return

        outBlack(textOutput, '>>> ' + cmd)

        cmd = p[0]
        p = ' '.join(p[1:])

        if cmd not in self.cmd_table:
            outRed(textOutput, 'Unknown cmd')
            return

        try:
            self.cmd_table[cmd](textOutput, p)
        except Exception, e:
            outRed(textOutput, str(e))
            return
