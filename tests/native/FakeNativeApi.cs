// Replaces only P/Invoke declarations when compiling the native test harness.
// No vendor DLL is linked or loaded by this executable.
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Web.Script.Serialization;

static partial class PrinterBridge {
    static int phase, count, initialModel, initialStatus, writeResult;
    static bool absentOnce, wrongBootloader, bootError, wrongFinalSerial;
    static string initialVersion, actualSerial, destination;
    static byte[] expectedPayload;
    static List<string> calls = new List<string>();

    static void Reset(string source, string target, byte[] payload) {
        phase=0; count=1; initialModel=source.StartsWith("DI-")?91:5;
        initialStatus=0x10001; writeResult=1;
        absentOnce=wrongBootloader=bootError=wrongFinalSerial=false;
        initialVersion=source; actualSerial="TEST-PRINTER"; destination=target;
        expectedPayload=payload; calls.Clear();
    }
    static int GetPrinterPortNum(IntPtr ports, ref int size) {
        if (phase==1 && absentOnce) { absentOnce=false; return -1; }
        for(int i=0;i<count;i++) {
            Marshal.WriteByte(ports,i*2,(byte)(phase==0?initialModel:phase==1?91:5));
            Marshal.WriteByte(ports,i*2+1,1);
        }
        return count;
    }
    static int CvGetStatus(int port) {
        return phase==0?initialStatus:phase==1?0x100001:bootError?0x100008:0x10001;
    }
    static int CvGetVersion(int port, ref string value) {
        value=phase==0?initialVersion:phase==1?(wrongBootloader?"OTHER_RW_1.00":"DI-RS1_RW_1.00"):"DS-RX1 "+destination;
        return value.Length;
    }
    static int CvGetSerialNo(int port, ref string value) {
        value=phase==2 && wrongFinalSerial?"OTHER-PRINTER":actualSerial; return value.Length;
    }
    static int CvGetColorDataVersion(int port, ref string value) { value="DI-RS1_300_0201.CWD"; return value.Length; }
    static int CvGetCounterL(int port) { return 100; }
    static int CvGetMediaCounter(int port) { return 50; }
    static int GetInitialMediaCount(int port) { return 400; }
    static int CvSetFirmwUpdateMode(int port) { calls.Add("enter"); phase=1; return 1; }
    static int SetFirmwDataWrite(int port, IntPtr data, int length) {
        calls.Add("write");
        byte[] bytes=new byte[length]; Marshal.Copy(data,bytes,0,length);
        Require(length==expectedPayload.Length,"payload length changed");
        for(int i=0;i<length;i++) if(bytes[i]!=expectedPayload[i]) throw new Exception("payload bytes changed");
        phase=2; return writeResult;
    }
    static void Delay(int milliseconds) { }
    static void Require(bool condition, string message) { if(!condition) throw new Exception(message); }
    static void Reject(Action action, int expectedWrites, string expectedMessage) {
        try { action(); throw new Exception("Expected rejection did not occur"); }
        catch(Exception error) {
            Require(error.Message.Contains(expectedMessage),"Unexpected error: "+error.Message);
            Require(calls.FindAll(x=>x=="write").Count==expectedWrites,"unexpected number of writes");
        }
    }
    public static int RunNativeTests(string root) {
        int passed=0;
        string[] sources={"DI-RS1 01.02","DS-RX1 02.04","DS-RX1 02.07","DS-RX1 02.10","DS-RX1 02.21"};
        string[] targets={"02.04","02.07","02.10","02.21","02.10"};
        for(int i=0;i<sources.Length;i++) {
            string path=Path.Combine(root,targets[i]+".bin"); byte[] payload=File.ReadAllBytes(path);
            Reset(sources[i],targets[i],payload);
            Flash(sources[i],"TEST-PRINTER",targets[i],path);
            Require(calls.Count==2 && calls[0]=="enter" && calls[1]=="write","incorrect command sequence");
            passed++;
        }
        string file=Path.Combine(root,"02.04.bin"); byte[] image=File.ReadAllBytes(file);
        Reset("DI-RS1 01.02","02.04",image);
        var output=new StringWriter(); var previous=Console.Out;
        try { Console.SetOut(output); Probe(); } finally { Console.SetOut(previous); }
        var printers=json.Deserialize<List<Dictionary<string,object>>>(output.ToString());
        Require((int)printers[0]["model"]==91 && (string)printers[0]["firmware"]=="DI-RS1 01.02", "DI detection failed");
        Require((string)printers[0]["serial"]=="TEST-PRINTER" && (int)printers[0]["counter"]==100,"DI details missing");
        Require(calls.Count==0,"probe wrote to device"); passed++;

        Reset("DI-RS1 01.02","02.04",image); absentOnce=true;
        Flash(initialVersion,actualSerial,"02.04",file); passed++;
        Reset("DI-RS1 01.02","02.04",image); initialModel=5;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),0,"identity"); passed++;
        Reset("DI-RS1 01.02","02.04",image); count=2;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),0,"identity"); passed++;
        Reset("DI-RS1 01.02","02.04",image); initialStatus=0x10002;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),0,"identity"); passed++;
        Reset("DI-RS1 01.02","02.04",image);
        Reject(()=>Flash(initialVersion,"WRONG-SERIAL","02.04",file),0,"identity"); passed++;
        Reset("DI-RS1 01.02","02.04",image);
        Reject(()=>Flash("DI-RS1 01.03",actualSerial,"02.04",file),0,"transition"); passed++;
        Reset("DI-RS1 01.02","02.04",image); wrongBootloader=true;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),0,"bootloader not detected"); passed++;
        Reset("DI-RS1 01.02","02.04",image); writeResult=0;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),1,"transfer failed"); passed++;
        Reset("DI-RS1 01.02","02.04",image); bootError=true;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),1,"Bootloader error"); passed++;
        Reset("DI-RS1 01.02","02.04",image); wrongFinalSerial=true;
        Reject(()=>Flash(initialVersion,actualSerial,"02.04",file),1,"serial number"); passed++;
        string corrupt=Path.GetTempFileName();
        try {
            byte[] altered=(byte[])image.Clone(); altered[100]^=1; File.WriteAllBytes(corrupt,altered);
            Reset("DI-RS1 01.02","02.04",image);
            Reject(()=>Flash(initialVersion,actualSerial,"02.04",corrupt),0,"checksum"); passed++;
        } finally { File.Delete(corrupt); }
        using (var held=new ManualResetEvent(false))
        using (var release=new ManualResetEvent(false)) {
            var owner=new Thread(()=> {
                using(var guard=new Mutex(false,"Local\\PrinterStudio.UsbOperation")) {
                    guard.WaitOne(); held.Set(); release.WaitOne(); guard.ReleaseMutex();
                }
            });
            owner.Start(); held.WaitOne();
            try {
                Reset("DI-RS1 01.02","02.04",image);
                Require(Main(new string[]{"flash",initialVersion,actualSerial,"02.04",file})==1,"concurrent USB writer was accepted");
                Require(calls.Count==0,"concurrent writer entered update mode");
                passed++;
            } finally { release.Set(); owner.Join(); }
        }
        Console.WriteLine(json.Serialize(new {status="passed",tests=passed,usb_access=false}));
        return 0;
    }
}

static class NativeBridgeTests {
    static int Main(string[] args) {
        try { return PrinterBridge.RunNativeTests(args[0]); }
        catch(Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
