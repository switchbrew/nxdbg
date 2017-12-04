# Copyright 2017 plutoo
import UsbConnection
from Adapter import *
from Utils import *
from AddressFormatter import *

class ThreadListAdapter(Adapter):
    def __init__(self, tree):
        self.tree = tree

    def onDbgEvent(self, event):
        if isinstance(event, UsbConnection.ThreadAttachEvent):
            addRow(self.tree, '%u' % event.thread_id, formatAddr(event.threadfunc), '0x%010x' % event.tls_ptr)
