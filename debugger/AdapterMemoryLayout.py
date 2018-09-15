# Copyright 2017 plutoo
from Adapter import *
from Utils import *

class AdapterMemoryLayout(Adapter):
    def __init__(self, usb, dbg_handle, tree):
        self.usb = usb
        self.dbg_handle = dbg_handle
        self.tree = tree

        self.refresh()

    def refresh(self):
        layout = []
        addr = 0
        while 1:
            ret = self.usb.cmdQueryMemory(self.dbg_handle, addr)
            if ret['type'] == 0x10:
                break
            layout.append(ret)
            addr = ret['addr'] + ret['size']

        self.tree.clear()
        for mapping in layout:
            if mapping['type'] != 0:
                addRow(self.tree,
                    '0x%010x' % mapping['addr'],
                    '0x%x' % mapping['size'],
                    memtypeToString(mapping['type']),
                    permToString(mapping['perm']))
