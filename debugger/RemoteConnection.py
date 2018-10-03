# Copyright 2017 plutoo
import sys
import struct
import threading
from Utils import *
from Types import *

class RemoteConnection:
    def __init__(self):
        self.lock = threading.Lock()

    def read(self, size):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def readResponse(self):
        result, size = struct.unpack('<II', self.read(0x8))
        buf = self.read(size)
        return {'rc': result, 'data': buf}

    def checkResult(self, resp):
        if resp['rc'] != 0:
            raise SwitchError('SwitchError 0x%x' % resp['rc'])

    ###
    ### Implementation of dbg commands starts here.
    ###

    def cmdListProcesses(self): # Cmd0
        with self.lock:
            self.write(struct.pack('<I', 0))
            resp = self.readResponse()

        self.checkResult(resp)

        pids = resp['data']
        pids = [pids[i*8 : i*8+8] for i in range(len(pids)/8)]
        pids = [struct.unpack('<Q', p)[0] for p in pids]

        return pids

    def cmdAttachProcess(self, pid): # Cmd1
        with self.lock:
            self.write(struct.pack('<I', 1))
            self.write(struct.pack('<Q', pid))
            resp = self.readResponse()

        self.checkResult(resp)

        handle = struct.unpack('<I', resp['data'])[0]
        return handle

    def cmdDetachProcess(self, handle): # Cmd2
        with self.lock:
            self.write(struct.pack('<I', 2))
            self.write(struct.pack('<I', handle))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdQueryMemory(self, handle, addr): # Cmd3
        with self.lock:
            self.write(struct.pack('<I', 3))
            self.write(struct.pack('<IIQ', handle, 0, addr))
            resp = self.readResponse()

        self.checkResult(resp)

        addr, size, perm, type_ = struct.unpack('<QQII', resp['data'])
        return  {'addr': addr, 'size': size, 'perm': perm, 'type': type_}

    def cmdGetDbgEvent(self, handle): # Cmd4
        with self.lock:
            self.write(struct.pack('<I', 4))
            self.write(struct.pack('<I', handle))
            resp = self.readResponse()

        self.checkResult(resp)
        return DebugEvent.from_raw(resp['data'])

    def cmdReadMemory(self, handle, addr, size): # Cmd5
        ret = ''
        for pos in range(0, size, 0x1000):
            chunk_size = min(0x1000, size-pos)

            with self.lock:
                self.write(struct.pack('<I', 5))
                self.write(struct.pack('<IIQ', handle, chunk_size, addr))

                resp = self.readResponse()
                self.checkResult(resp)
                ret += resp['data']

        return ret

    def cmdContinueDbgEvent(self, handle, flags, thread_id): # Cmd6
        with self.lock:
            self.write(struct.pack('<I', 6))
            self.write(struct.pack('<IIQ', handle, flags, thread_id))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdGetThreadContext(self, handle, thread_id, flags): # Cmd7
        with self.lock:
            self.write(struct.pack('<I', 7))
            self.write(struct.pack('<IIQ', handle, flags, thread_id))
            resp = self.readResponse()

        self.checkResult(resp)
        return resp['data']

    def cmdBreakProcess(self, handle): # Cmd8
        with self.lock:
            self.write(struct.pack('<I', 8))
            self.write(struct.pack('<I', handle))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdWriteMemory32(self, handle, addr, val): # Cmd9
        with self.lock:
            self.write(struct.pack('<I', 9))
            self.write(struct.pack('<IIQ', handle, val, addr))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdListenForAppLaunch(self): # Cmd10
        with self.lock:
            self.write(struct.pack('<I', 10))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdGetAppPid(self): # Cmd11
        with self.lock:
            self.write(struct.pack('<I', 11))
            resp = self.readResponse()

        try:
            self.checkResult(resp)
        except:
            return None

        return struct.unpack('<Q', resp['data'])[0]

    def cmdStartProcess(self, pid): # Cmd12
        with self.lock:
            self.write(struct.pack('<I', 12))
            self.write(struct.pack('<Q', pid))
            resp = self.readResponse()

        self.checkResult(resp)

    def cmdGetTitlePid(self, titleid): # Cmd13
        with self.lock:
            self.write(struct.pack('<I', 13))
            self.write(struct.pack('<Q', titleid))
            resp = self.readResponse()

        self.checkResult(resp)
        return struct.unpack('<Q', resp['data'])[0]
