# Copyright 2017 plutoo
from PyQt4 import QtGui, QtCore

def requiresContinue(event):
    return (event.flags & 1) if event else False

def hexdump(src, length=16, base=0):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in xrange(0, len(src), length):
        chars = src[c:c+length]
        hex = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
        lines.append("%04x  %-*s  %s\n" % (base+c, length*3, hex, printable))
    return ''.join(lines)

def permToString(perm):
    ret = ''
    ret += 'R' if (perm & 1) else '-'
    ret += 'W' if (perm & 2) else '-'
    ret += 'X' if (perm & 4) else '-'
    return ret

def memtypeToString(type_):
    table = {
        0: 'Unmapped',
        1: 'IO',
        2: 'Normal',
        3: 'CodeStatic',
        4: 'CodeMutable',
        5: 'Heap',
        6: 'SharedMemory',
        7: 'WeirdSharedMemory',
        8: 'ModuleCodeStatic',
        9: 'ModuleCodeMutable',
        10: 'IpcBuffer0',
        11: 'MappedMemory',
        12: 'ThreadLocal',
        13: 'TransferMemoryIsolated',
        14: 'TransferMemory',
        15: 'ProcessMemory',
        16: 'Reserved',
        17: 'IpcBuffer1',
        18: 'IpcBuffer3',
    }
    try:
        return table[type_]
    except:
        return 'Unknown'

def addRow(tree, *args):
    item = QtGui.QTreeWidgetItem(args)
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
    tree.addTopLevelItems([item])
