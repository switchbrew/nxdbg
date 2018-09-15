import struct

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
