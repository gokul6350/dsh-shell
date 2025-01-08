#include <windows.h>
#include <stdio.h>

typedef struct {
    HANDLE hPC;
    HANDLE hPipeIn;
    HANDLE hPipeOut;
} TerminalHandle;

__declspec(dllexport) TerminalHandle* create_terminal() {
    SECURITY_ATTRIBUTES sa = {0};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    HANDLE hPipeInRead, hPipeInWrite;
    HANDLE hPipeOutRead, hPipeOutWrite;

    // Create pipes
    CreatePipe(&hPipeInRead, &hPipeInWrite, &sa, 0);
    CreatePipe(&hPipeOutRead, &hPipeOutWrite, &sa, 0);

    // Create process
    STARTUPINFO si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = hPipeInRead;
    si.hStdOutput = hPipeOutWrite;
    si.hStdError = hPipeOutWrite;

    wchar_t cmdLine[] = L"cmd.exe";
    CreateProcessW(
        NULL,
        cmdLine,
        NULL,
        NULL,
        TRUE,
        CREATE_NO_WINDOW,
        NULL,
        NULL,
        &si,
        &pi
    );

    TerminalHandle* handle = (TerminalHandle*)malloc(sizeof(TerminalHandle));
    handle->hPC = pi.hProcess;
    handle->hPipeIn = hPipeInWrite;
    handle->hPipeOut = hPipeOutRead;

    CloseHandle(hPipeInRead);
    CloseHandle(hPipeOutWrite);
    CloseHandle(pi.hThread);

    return handle;
}

__declspec(dllexport) int write_terminal(TerminalHandle* handle, const char* data, int length) {
    DWORD written;
    return WriteFile(handle->hPipeIn, data, length, &written, NULL);
}

__declspec(dllexport) int read_terminal(TerminalHandle* handle, char* buffer, int buffer_size) {
    DWORD read;
    if (ReadFile(handle->hPipeOut, buffer, buffer_size, &read, NULL)) {
        return read;
    }
    return 0;
}

__declspec(dllexport) void close_terminal(TerminalHandle* handle) {
    TerminateProcess(handle->hPC, 0);
    CloseHandle(handle->hPC);
    CloseHandle(handle->hPipeIn);
    CloseHandle(handle->hPipeOut);
    free(handle);
} 