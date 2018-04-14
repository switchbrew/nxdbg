# Copyright 2017 plutoo
formatterSingleton = None

def getNsos():
    return formatterSingleton.getNsos()

def formatAddr(addr, pad=0):
    if formatterSingleton is None:
        return defaultFormatAddr(addr, pad)

    return formatterSingleton.formatAddr(addr, pad)

def defaultFormatAddr(addr, pad):
    return ('0x%%0%dx' % pad) % addr

class AddressFormatter:
    def __init__(self, usb, dbg_handle):
        self.usb = usb
        self.dbg_handle = dbg_handle

        self.nsos = {}
        self.refresh()

        global formatterSingleton
        formatterSingleton = self

    def refresh(self):
        modules = []

        addr = 0
        while 1:
            ret = self.usb.cmdQueryMemory(self.dbg_handle, addr)
            if ret['type'] == 0x10:
                break
            if ret['type'] == 3 and ret['perm'] == 0b101:
                modules.append({'addr': ret['addr'], 'size': ret['size']})
            if (ret['type'] == 3 and ret['perm'] == 0b001) or ret['type'] == 4:
                modules[-1]['size'] += ret['size']
            addr = ret['addr'] + ret['size']

        if len(modules) == 1:
            self.nsos['main'] = modules[0]
        elif len(modules) > 1:
            self.nsos['rtld'] = modules[0]
            self.nsos['main'] = modules[1]

            if len(modules) > 2:
                self.nsos['sdk'] = modules[2]

                if len(modules) > 3:
                    for i in range(len(modules)-3):
                        self.nsos['subsdk%d' % i] = modules[2]

    def formatAddr(self, addr, pad):
        for n in self.nsos:
            nso = self.nsos[n]
            if addr >= nso['addr'] and addr < (nso['addr'] + nso['size']):
                return '%s+0x%x' % (n, addr-nso['addr'])

        return defaultFormatAddr(addr, pad)

    def getNsos(self):
        return self.nsos
