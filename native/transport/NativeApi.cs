using System;
using System.Runtime.InteropServices;
using System.Threading;

static partial class PrinterBridge {
    const string Dll = "cspstat64.dll";
    [DllImport(Dll, ExactSpelling=true)] static extern int GetPrinterPortNum(IntPtr ports, ref int size);
    [DllImport(Dll, ExactSpelling=true)] static extern int CvGetStatus(int port);
    [DllImport(Dll, ExactSpelling=true)] static extern int CvSetFirmwUpdateMode(int port);
    [DllImport(Dll, ExactSpelling=true)] static extern int SetFirmwDataWrite(int port, IntPtr data, int length);
    [DllImport(Dll, CharSet=CharSet.Ansi, ExactSpelling=true)] static extern int CvGetVersion(int port, [MarshalAs(UnmanagedType.VBByRefStr)] ref string value);
    [DllImport(Dll, CharSet=CharSet.Ansi, ExactSpelling=true)] static extern int CvGetSerialNo(int port, [MarshalAs(UnmanagedType.VBByRefStr)] ref string value);
    [DllImport(Dll, CharSet=CharSet.Ansi, ExactSpelling=true)] static extern int CvGetColorDataVersion(int port, [MarshalAs(UnmanagedType.VBByRefStr)] ref string value);
    [DllImport(Dll, ExactSpelling=true)] static extern int CvGetCounterL(int port);
    [DllImport(Dll, ExactSpelling=true)] static extern int CvGetMediaCounter(int port);
    [DllImport(Dll, ExactSpelling=true)] static extern int GetInitialMediaCount(int port);
    static void Delay(int milliseconds) { Thread.Sleep(milliseconds); }
}
