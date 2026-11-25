# Start a process outside the current job object (CREATE_BREAKAWAY_FROM_JOB; the T3 job allows breakaway), with no
# window, so it does not depend on the T3 session or a tool-call lifetime. Prints the new PID.
#   & E:\CSC2108Local\ops\detach.ps1 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\...\watchdog.ps1 ...'
param([Parameter(Mandatory = $true)][string]$CommandLine, [string]$WorkingDirectory = 'E:\CSC2108Local')
if (-not ('Detach.Native' -as [type])) {
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
namespace Detach {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct STARTUPINFO {
    public int cb; public string lpReserved; public string lpDesktop; public string lpTitle; public int dwX; public int dwY;
    public int dwXSize; public int dwYSize; public int dwXCountChars; public int dwYCountChars; public int dwFillAttribute;
    public int dwFlags; public short wShowWindow; public short cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput;
    public IntPtr hStdOutput; public IntPtr hStdError; }
  [StructLayout(LayoutKind.Sequential)] public struct PROCESS_INFORMATION { public IntPtr hProcess; public IntPtr hThread; public int dwProcessId; public int dwThreadId; }
  public static class Native {
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    public static extern bool CreateProcess(string app, string cmd, IntPtr pa, IntPtr ta, bool inherit, uint flags, IntPtr env, string cwd, ref STARTUPINFO si, out PROCESS_INFORMATION pi);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
    public static int Start(string cmd, string cwd) {
      STARTUPINFO si = new STARTUPINFO(); si.cb = Marshal.SizeOf(si); PROCESS_INFORMATION pi;
      uint flags = 0x01000000 | 0x08000000 | 0x00000200; // BREAKAWAY_FROM_JOB | NO_WINDOW | NEW_PROCESS_GROUP
      if (!CreateProcess(null, cmd, IntPtr.Zero, IntPtr.Zero, false, flags, IntPtr.Zero, cwd, ref si, out pi))
        throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
      CloseHandle(pi.hThread); CloseHandle(pi.hProcess); return pi.dwProcessId; }
  }
}
'@
}
[Detach.Native]::Start($CommandLine, $WorkingDirectory)
