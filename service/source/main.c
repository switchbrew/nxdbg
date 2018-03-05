// Copyright 2017 plutoo
#include <switch.h>

u32 __nx_applet_type = AppletType_None;

static char g_heap[0x20000];

void __libnx_initheap(void)
{
    extern char* fake_heap_start;
    extern char* fake_heap_end;

    fake_heap_start = &g_heap[0];
    fake_heap_end   = &g_heap[sizeof g_heap];
}

typedef enum {
    REQ_LIST_PROCESSES   =0,
    REQ_ATTACH_PROCESS   =1,
    REQ_DETACH_PROCESS   =2,
    REQ_QUERYMEMORY      =3,
    REQ_GET_DBGEVENT     =4,
    REQ_READMEMORY       =5,
    REQ_CONTINUE_DBGEVENT=6,
    REQ_GET_THREADCONTEXT=7,
    REQ_BREAK_PROCESS    =8,
    REQ_WRITEMEMORY32    =9,
    REQ_LISTENAPPLAUNCH  =10,
    REQ_GETAPPPID        =11,
    REQ_START_PROCESS    =12,
    REQ_GET_TITLE_PID    =13
} RequestType;

typedef struct {
    u32 Type;
} DebuggerRequest;

typedef struct {
    u32 Result;
    u32 LenBytes;
    void* Data;
} DebuggerResponse;


typedef struct { // Cmd1
    u64 Pid;
} AttachProcessReq;

typedef struct {
    u32 DbgHandle;
} AttachProcessResp;

typedef struct { // Cmd2
    u32 DbgHandle;
} DetachProcessReq;

typedef struct { // Cmd3
    u32 DbgHandle;
    u32 Pad;
    u64 Addr;
} QueryMemoryReq;

typedef struct {
    u64 Addr;
    u64 Size;
    u32 Perm;
    u32 Type;
} QueryMemoryResp;

typedef struct { // Cmd4
    u32 DbgHandle;
} GetDbgEventReq;

typedef struct {
    u8 Event[0x40];
} GetDbgEventResp;

typedef struct { // Cmd5
    u32 DbgHandle;
    u32 Size;
    u64 Addr;
} ReadMemoryReq;

typedef struct { // Cmd6
    u32 DbgHandle;
    u32 Flags;
    u64 ThreadId;
} ContinueDbgEventReq;

typedef struct { // Cmd7
    u32 DbgHandle;
    u32 Flags;
    u64 ThreadId;
} GetThreadContextReq;

typedef struct {
    u8 Out[0x320];
} GetThreadContextResp;

typedef struct { // Cmd8
    u32 DbgHandle;
} BreakProcessReq;

typedef struct { // Cmd9
    u32 DbgHandle;
    u32 Value;
    u64 Addr;
} WriteMemory32Req;

typedef struct { // Cmd11
    u64 Pid;
} GetAppPidResp;

typedef struct { // Cmd12
    u64 Pid;
} StartProcessReq;

typedef struct { // Cmd13
    u64 TitleId;
} GetTitlePidReq;

typedef struct {
    u64 Pid;
} GetTitlePidResp;


void sendUsbResponse(DebuggerResponse resp) {
    usbCommsWrite((void*)&resp, 8);

    if (resp.LenBytes > 0)
        usbCommsWrite(resp.Data, resp.LenBytes);
}

int handleUsbCommand() {
    DebuggerRequest r;
    DebuggerResponse resp;
    Result rc;

    size_t len = usbCommsRead(&r, sizeof(r));
    if (len != sizeof(r))
        // USB transfer failure.
        fatalSimple(222 | (1 << 9));

    resp.LenBytes = 0;
    resp.Data = NULL;

    switch (r.Type) {
    case REQ_LIST_PROCESSES: { // Cmd0
        static u64 pids[256];
        u32 numOut = 256;

        rc = svcGetProcessList(&numOut, pids, numOut);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = numOut * sizeof(u64);
            resp.Data = &pids[0];
        }

        sendUsbResponse(resp);
        break;
    }
    case REQ_ATTACH_PROCESS: { // Cmd1
        AttachProcessReq   req_;
        AttachProcessResp  resp_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcDebugActiveProcess(&resp_.DbgHandle, req_.Pid);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_DETACH_PROCESS: { // Cmd2
        DetachProcessReq req_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcCloseHandle(req_.DbgHandle);
        resp.Result = rc;

        sendUsbResponse(resp);
        break;
    }

    case REQ_QUERYMEMORY: { // Cmd3
        QueryMemoryReq   req_;
        QueryMemoryResp  resp_;
        usbCommsRead(&req_, sizeof(req_));

        MemoryInfo info;
        u32 who_cares;
        rc = svcQueryDebugProcessMemory(&info, &who_cares, req_.DbgHandle, req_.Addr);
        resp.Result = rc;

        if (rc == 0) {
            resp_.Addr = info.addr;
            resp_.Size = info.size;
            resp_.Type = info.type;
            resp_.Perm = info.perm;

            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_GET_DBGEVENT: { // Cmd4
        GetDbgEventReq   req_;
        GetDbgEventResp  resp_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcGetDebugEvent(&resp_.Event[0], req_.DbgHandle);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_READMEMORY: { // Cmd5
        ReadMemoryReq req_;
        usbCommsRead(&req_, sizeof(req_));

        if (req_.Size > 0x1000)
            // Too big read.
            fatalSimple(222 | (5 << 9));

        static u8 page[0x1000];
        rc = svcReadDebugProcessMemory(page, req_.DbgHandle, req_.Addr, req_.Size);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = req_.Size;
            resp.Data = &page[0];
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_CONTINUE_DBGEVENT: { // Cmd6
        ContinueDbgEventReq req_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcContinueDebugEvent(req_.DbgHandle, req_.Flags, req_.ThreadId);
        resp.Result = rc;

        sendUsbResponse(resp);
        break;
    }

    case REQ_GET_THREADCONTEXT: { // Cmd7
        GetThreadContextReq   req_;
        GetThreadContextResp  resp_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcGetDebugThreadContext(&resp_.Out[0], req_.DbgHandle, req_.ThreadId, req_.Flags);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_BREAK_PROCESS: { // Cmd8
        BreakProcessReq req_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcBreakDebugProcess(req_.DbgHandle);
        resp.Result = rc;

        sendUsbResponse(resp);
        break;
    }

    case REQ_WRITEMEMORY32: { // Cmd9
        WriteMemory32Req req_;
        usbCommsRead(&req_, sizeof(req_));

        rc = svcWriteDebugProcessMemory(req_.DbgHandle, (void*)&req_.Value, req_.Addr, 4);
        resp.Result = rc;

        sendUsbResponse(resp);
        break;
    }

    case REQ_LISTENAPPLAUNCH: { // Cmd10
        Handle h;
        rc = pmdmntEnableDebugForApplication(&h);
        resp.Result = rc;

        if (rc == 0)
            svcCloseHandle(h);

        sendUsbResponse(resp);
        break;
    }

    case REQ_GETAPPPID: { // Cmd11
        GetAppPidResp resp_;

        rc = pmdmntGetApplicationPid(&resp_.Pid);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    case REQ_START_PROCESS: { // Cmd12
        StartProcessReq req_;
        usbCommsRead(&req_, sizeof(req_));

        rc = pmdmntStartProcess(req_.Pid);
        resp.Result = rc;

        sendUsbResponse(resp);
        break;
    }

    case REQ_GET_TITLE_PID: { // Cmd13
        GetTitlePidReq   req_;
        GetTitlePidResp  resp_;
        usbCommsRead(&req_, sizeof(req_));

        rc = pmdmntGetTitlePid(&resp_.Pid, req_.TitleId);
        resp.Result = rc;

        if (rc == 0) {
            resp.LenBytes = sizeof(resp_);
            resp.Data = &resp_;
        }

        sendUsbResponse(resp);
        break;
    }

    default:
        // Unknown request.
        fatalSimple(222 | (2 << 9));
    }

    return 1;
}

int main(int argc, char *argv[])
{
    Result rc;

    rc = pmdmntInitialize();
    if (rc)
        // Failed to get PM debug interface.
        fatalSimple(222 | (6 << 9));

    rc = usbCommsInitialize();
    if (rc)
        fatalSimple(rc);

    while (handleUsbCommand());

    return 0;
}

