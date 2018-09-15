# Copyright 2017 plutoo
import AddressFormatter
from Types import *
from Adapter import *
from Utils import *

class AdapterThreadList(Adapter):
    def __init__(self, tree):
        self.tree = tree

    def onDbgEvent(self, event):
        if isinstance(event, ThreadAttachEvent):
            addRow(self.tree, '%u' % event.thread_id, AddressFormatter.formatAddr(event.threadfunc), '0x%010x' % event.tls_ptr)
