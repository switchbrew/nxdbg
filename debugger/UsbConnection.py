# Copyright 2017 plutoo
import usb
import sys
import struct
import threading
from Utils import *

def sanitizeString(s):
    p = s.find('\0')
    if p == -1:
        return s
    else:
        return s[:p]

class SwitchError(Exception):
    pass

class DebugEvent:
    @staticmethod
    def from_raw(data):
        header = data[:0x10]
        specifics = data[0x10:]

        type_ = struct.unpack('<I', header[:4])[0]
        if type_ == 0:
            return ProcessAttachEvent(header, specifics)
        if type_ == 1:
            return ThreadAttachEvent(header, specifics)
        if type_ == 2:
            return Unknown2Event(header, specifics)
        if type_ == 3:
            return ExitEvent(header, specifics)
        if type_ == 4:
            return ExceptionEvent.from_raw(header, specifics)

        raise NotImplementedError()

    def __init__(self, header):
        type_, flags, thread_id = struct.unpack('<IIQ', header)
        self.type_ = type_
        self.flags = flags
        self.thread_id = thread_id


class ProcessAttachEvent(DebugEvent):
    def __init__(self, header, specifics):
        DebugEvent.__init__(self, header)

        title_id, pid, name, mmuflags = struct.unpack('<QQ12sI', specifics[:0x20])
        self.title_id = title_id
        self.pid = pid
        self.name = sanitizeString(name)
        self.mmuflags = mmuflags

    def __repr__(self):
        return '[ProcessAttach] Name: %s TitleId: 0x%016x Pid: %u' \
            % (self.name, self.title_id, self.pid)

class ThreadAttachEvent(DebugEvent):
    def __init__(self, header, specifics):
        DebugEvent.__init__(self, header)

        thread_id, tls_ptr, threadfunc = struct.unpack('<QQQ', specifics[:0x18])
        self.thread_id_new = thread_id
        self.tls_ptr = tls_ptr
        self.threadfunc = threadfunc

    def __repr__(self):
        return '[ThreadAttach] Tid: %u ThreadFunc: 0x%010x TlsPointer: 0x%010x' \
            % (self.thread_id_new, self.threadfunc, self.tls_ptr)

class Unknown2Event(DebugEvent):
    def __init__(self, header, specifics):
        DebugEvent.__init__(self, header)

    def __repr__(self):
        return '[Unknown2Event]'

class ExitEvent(DebugEvent):
    def __init__(self, header, specifics):
        DebugEvent.__init__(self, header)

        exit_type = struct.unpack('<Q', specifics[:8])
        self.exit_type = exit_type

    def __repr__(self):
        return '[ExitEvent] Type: %u' % self.exit_type

class ExceptionType:
    UndefinedInstruction=0  # extra_shit = opcode
    InstructionAbort=1      # extra_shit = 0
    DataAbortMisc=2         # extra_shit = 0
    PcSpAlignmentFault=3    # extra_shit = 0
    DebuggerAttached=4
    BreakPoint=5            # extra_shit = is_hw_watchpoint
    UserBreak=6
    DebuggerBreak=7
    BadSvcId=8              # extra_shit = svc_id

class ExceptionEvent(DebugEvent):
    @staticmethod
    def from_raw(header, specifics):
        exception_type, fault_reg, per_exception = struct.unpack('<QQQ', specifics[:0x18])

        if exception_type == 0:
            return ExceptionUndefinedInstruction(header, exception_type, fault_reg, per_exception)
        if exception_type == 1:
            return ExceptionInstructionAbort(header, exception_type, fault_reg, per_exception)
        if exception_type == 2:
            return ExceptionDataAbortMisc(header, exception_type, fault_reg, per_exception)
        if exception_type == 3:
            return ExceptionPcSpAlignmentFault(header, exception_type, fault_reg, per_exception)
        if exception_type == 4:
            return ExceptionDebuggerAttached(header, exception_type, fault_reg, per_exception)
        if exception_type == 5:
            return ExceptionBreakPoint(header, exception_type, fault_reg, per_exception)
        if exception_type == 6:
            return ExceptionUserBreak(header, exception_type, fault_reg, per_exception)
        if exception_type == 7:
            return ExceptionDebuggerBreak(header, exception_type, fault_reg, per_exception)
        if exception_type == 8:
            return ExceptionBadSvcId(header, exception_type, fault_reg, per_exception)

    def __init__(self, header, exception_type, fault_reg, per_exception):
        DebugEvent.__init__(self, header)
        self.fault_reg = fault_reg
        self.per_exception = per_exception

class ExceptionUndefinedInstruction(ExceptionEvent):
    def __repr__(self):
        return '[UndefinedInstruction] Tid: %u Faultreg: 0x%010x Opcode: 0x%x' % (self.thread_id, self.fault_reg, self.per_exception)

class ExceptionInstructionAbort(ExceptionEvent):
    def __repr__(self):
        return '[InstructionAbort] Tid: %u Address: 0x%010x' % (self.thread_id, self.fault_reg)

class ExceptionDataAbortMisc(ExceptionEvent):
    def __repr__(self):
        return '[DataAbortMisc] Tid: %u Address: 0x%010x' % (self.thread_id, self.fault_reg)

class ExceptionPcSpAlignmentFault(ExceptionEvent):
    def __repr__(self):
        return '[PcSpAlignmentFault] Tid: %u Faultreg: 0x%010x' % (self.thread_id, self.fault_reg)

class ExceptionDebuggerAttached(ExceptionEvent):
    def __repr__(self):
        return '[DebuggerAttached]'

class ExceptionBreakPoint(ExceptionEvent):
    def __repr__(self):
        return '[BreakPoint Tid: %u IsWatchdog: %s]' % (self.thread_id, 'True' if self.per_exception else 'False')

class ExceptionUserBreak(ExceptionEvent):
    def __repr__(self):
        return '[UserBreak Tid: %u <not implemented>]' % (self.thread_id)

class ExceptionDebuggerBreak(ExceptionEvent):
    def __repr__(self):
        return '[DebuggerBreak]'

class ExceptionBadSvcId(ExceptionEvent):
    def __repr__(self):
        return '[BadSvcId Tid: %u SvcId: 0x%x]'


class UsbConnection:
    def __init__(self):
        self.lock = threading.Lock()

        self.dev = usb.core.find(idVendor=0x057e, idProduct=0x3000)
        if self.dev is None:
            raise Exception('Device not found')

        self.dev.set_configuration()
        self.cfg = self.dev.get_active_configuration()
        self.intf = self.cfg[(0,0)]

        self.ep_in = usb.util.find_descriptor(
            self.intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)
        assert self.ep_in is not None

        self.ep_out = usb.util.find_descriptor(
            self.intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        assert self.ep_out is not None

    def read(self, size):
        data = ""
        while size != 0:
            tmp_data = self.ep_in.read(size)
            tmp_data = ''.join([chr(x) for x in tmp_data])
            size -= len(tmp_data)
            data+= tmp_data
        return data

    def write(self, data):
        size = len(data)
        tmplen = 0;
        while size != 0:
            tmplen = self.ep_out.write(data)
            size -= tmplen
            data = data[tmplen:]

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

                ret += self.readResponse()
                self.checkResult(resp)

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
