# Copyright 2017 plutoo
from capstone import *

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

def rightpad(s, n):
    return s + ' '*max(n-len(s), 0)

def Dis(addr, code):
    global md
    ret = ''
    for i in md.disasm(code, addr):
        ret += '0x%010x:  %s %s\n' % (i.address, rightpad(i.mnemonic, 7), i.op_str)
    return ret
