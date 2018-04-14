# Copyright 2017 plutoo
import UsbConnection
import AddressFormatter
from Adapter import *
from Utils import *

class ThreadListAdapter(Adapter):
    def __init__(self, tree):
        self.tree = tree

    def onDbgEvent(self, event):
        if isinstance(event, UsbConnection.ThreadAttachEvent):
            addRow(self.tree, '%u' % event.thread_id, AddressFormatter.formatAddr(event.threadfunc), '0x%010x' % event.tls_ptr)
