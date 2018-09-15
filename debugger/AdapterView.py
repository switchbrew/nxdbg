# Copyright 2017 plutoo
import struct
from Adapter import *
from Utils import *
from Lazy import *

class AdapterView(Adapter):
    def __init__(self, usb, dbg_handle, expr_eval, lineCmdView, textOutputView):
        self.usb = usb
        self.dbg_handle = dbg_handle

        self.expr_eval = expr_eval
        self.lineCmd = lineCmdView
        self.textOutput = textOutputView

        self.lineCmd.returnPressed.connect(self.refresh)

    def refresh(self):
        self.expr_eval.execute(self.textOutput, self.lineCmd)

    def onDbgEvent(self, event):
        if event:
            self.refresh()
