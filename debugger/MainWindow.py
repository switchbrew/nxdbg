# Copyright 2017 plutoo
from PyQt4 import QtGui
from PyQt4.QtCore import QThread, SIGNAL
import sys
import time
import threading
import mainwindow_gen
import ArmDisassembler
from UsbConnection import *
from Utils import *
from Lazy import *
from Playground import *
from ExpressionEval import *
from BreakpointManager import *
from AddressFormatter import *
from MemoryLayoutAdapter import *
from ThreadListAdapter import *
from StateLabelAdapter import *
from RegistersAdapter import *
from StackTraceAdapter import *
from ViewAdapter import *

class UsbThread(QThread):
    def __init__(self, usb, dbg_handle):
        QThread.__init__(self)
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.event = threading.Event()

    def __del__(self):
        self.wait()

    def run(self):
        while 1:
            try:
                event = self.usb.cmdGetDbgEvent(self.dbg_handle)

                self.event.clear()
                self.emit(SIGNAL('onDbgEvent(PyQt_PyObject)'), event)
                self.event.wait()

            except SwitchError:
                pass
            time.sleep(0.1)


class MainDebugger(QtGui.QMainWindow, mainwindow_gen.Ui_MainWindow):
    def __init__(self, usb, dbg_handle, parent=None):
        super(MainDebugger, self).__init__(parent)
        self.setupUi(self)

        self.active_event = None

        self.usb = usb
        self.dbg_handle = dbg_handle
        self.usb_thread = UsbThread(usb, dbg_handle)

        AddressFormatter(self.usb, self.dbg_handle)

        self.bp_manager = BreakpointManager(self.usb, self.dbg_handle, self.treeBreakpoints)
        expr_eval = ExpressionEvaluator(self.usb, self.dbg_handle, self)
        self.expr_eval = expr_eval

        self.adapters = []
        self.adapters.append(Lazy(usb, dbg_handle))
        self.adapters.append(MemoryLayoutAdapter(usb, dbg_handle, self.treeMemory))
        self.adapters.append(ThreadListAdapter(self.treeThreads))
        self.adapters.append(StateLabelAdapter(self.labelState))
        self.adapters.append(RegistersAdapter(usb, dbg_handle, self))
        self.adapters.append(StackTraceAdapter(usb, dbg_handle, self.treeStackTrace))
        self.adapters.append(ViewAdapter(usb, dbg_handle, expr_eval, self.lineCmdView0, self.textOutputView0))
        self.adapters.append(ViewAdapter(usb, dbg_handle, expr_eval, self.lineCmdView1, self.textOutputView1))
        self.adapters.append(ViewAdapter(usb, dbg_handle, expr_eval, self.lineCmdView2, self.textOutputView2))
        self.adapters.append(Playground(usb, dbg_handle, self))

        self.connect(self.usb_thread, SIGNAL('onDbgEvent(PyQt_PyObject)'), self.onDbgEvent)
        self.usb_thread.start()

        self.lineCmd.returnPressed.connect(self.onUserCmd)

    def onUserCmd(self):
        self.expr_eval.execute(self.textOutput, self.lineCmd)
        self.lineCmd.setText('')

    def closeEvent(self, event):
        self.bp_manager.cleanup()
        self.usb.cmdContinueDbgEvent(self.dbg_handle, 4|2|1, 0)
        self.usb.cmdDetachProcess(self.dbg_handle)
        event.accept()

    def outGrey(self, text):
        self.textOutput.setTextColor(QtGui.QColor(0x77, 0x77, 0x77))
        self.textOutput.append(text)

    def outRed(self, text):
        self.textOutput.setTextColor(QtGui.QColor(0xFF, 0x33, 0x33))
        self.textOutput.append(text)

    def outBlack(self, text):
        self.textOutput.setTextColor(QtGui.QColor(0, 0, 0))
        self.textOutput.append(text)

    def onDbgEvent(self, event):
        assert self.active_event is None
        self.active_event = event
        self.dispatchDbgEvent(event)

    def continueDbgEvent(self):
        if self.active_event and requiresContinue(self.active_event):
            self.bp_manager.continueDbgEvent()

            try:
                self.usb.cmdContinueDbgEvent(self.dbg_handle, 4|2|1, 0)
            except SwitchError:
                pass

        self.active_event = None
        self.dispatchDbgEvent(None)
        self.usb_thread.event.set()

    def requestContinue(self):
        self.continueRequested = True

    def dispatchDbgEvent(self, event):
        if event:
            self.outGrey(repr(event))

        self.bp_manager.onDbgEvent(event)
        self.continueRequested = False

        for a in self.adapters:
            a.onDbgEvent(event)

        if self.continueRequested:
            self.continueDbgEvent()
            return

        '''
        if isinstance(event, ProcessAttachEvent):
            self.continueDbgEvent()
        '''
        if isinstance(event, ThreadAttachEvent):
            self.continueDbgEvent()

def main(argv):
    usb = None
    dbg_handle = None

    if argv[1] == '--pid':
        pid = int(argv[2])
        usb = UsbConnection()
        dbg_handle = usb.cmdAttachProcess(pid)

    if argv[1] == '--titleid':
        titleid = int(argv[2], 0)
        usb = UsbConnection()
        pid = usb.cmdGetTitlePid(titleid)
        dbg_handle = usb.cmdAttachProcess(pid)

    elif argv[1] == '--nextlaunch':
        usb = UsbConnection()
        usb.cmdListenForAppLaunch()

        pid = None
        while pid is None:
            print 'Waiting for launch..'
            time.sleep(1)
            pid = usb.cmdGetAppPid()

        dbg_handle = usb.cmdAttachProcess(pid)
        usb.cmdStartProcess(pid)

    else:
        print 'Usage: %s [--pid <pid>] || [--nextlaunch] || --titleid <tid>' % argv[0]
        return

    try:
        app = QtGui.QApplication(argv)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
        form = MainDebugger(usb, dbg_handle)
        form.show()
        app.exec_()
    except:
        usb.cmdDetachProcess(dbg_handle)
        raise
    return 0

sys.exit(main(sys.argv))
