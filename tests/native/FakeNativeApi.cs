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
    static readonly string UsbMutexName="Local\\PrinterStudio.Tests."+System.Diagnostics.Process.GetCurrentProcess().Id;
    static int phase, count, initialModel, initialStatus, writeResult;
    static bool absentOnce, wrongBootloader, bootError, wrongFinalSerial;
    static string initialVersion, actualSerial, destination;
    static byte[] expectedPayload;
    static byte[] fakeNor;
    static int readCount;
    static int failReadAfter;
    static bool wrongDiBoot, invalidNorResponse;
    static List<string> calls = new List<string>();

    static void Reset(string source, string target, byte[] payload) {
        phase=0; count=1; initialModel=source.StartsWith("DI-")?91:5;
        initialStatus=0x10001; writeResult=1;
        absentOnce=wrongBootloader=bootError=wrongFinalSerial=false;
        initialVersion=source; actualSerial="TEST-PRINTER"; destination=target;
        expectedPayload=payload; calls.Clear();
        readCount=0; failReadAfter=0; wrongDiBoot=invalidNorResponse=false;
    }
    static int GetPrinterPortNum(IntPtr ports, ref int size) {
        if (phase==1 && absentOnce) { absentOnce=false; return -1; }
        for(int i=0;i<count;i++) {
            Marshal.WriteByte(ports,i*2,(byte)(phase==0?initialModel:phase==1?91:destination==DiTarget?91:5));
            Marshal.WriteByte(ports,i*2+1,1);
        }
        return count;
    }
    static int CvGetStatus(int port) {
        return phase==0?initialStatus:phase==1?0x100001:bootError?0x100008:0x10001;
    }
    static int CvGetVersion(int port, ref string value) {
        value=phase==0?initialVersion:phase==1?(wrongBootloader?"OTHER_RW_1.00":"DI-RS1_RW_1.00"):destination==DiTarget?DiTarget:destination==VgTarget?"DS-RX1 02.21":"DS-RX1 "+destination;
        return value.Length;
    }
    static int CvGetSerialNo(int port, ref string value) {
        value=phase==2 && wrongFinalSerial?"OTHER-PRINTER":actualSerial; return value.Length;
    }
    static int CvGetColorDataVersion(int port, ref string value) { value="DI-RS1_300_0201.CWD"; return value.Length; }
    static int CvGetCounterL(int port) { return 100; }
    static int CvGetMediaCounter(int port) { return 50; }
    static int GetInitialMediaCount(int port) { return 400; }
    static void PrepareFakeNor() {
        fakeNor=new byte[0x200000];
        for(int i=0;i<fakeNor.Length;i++) fakeNor[i]=255;
        byte[] boot=Encoding.ASCII.GetBytes("DIRS1_BOOT 1.00"); Array.Copy(boot,0,fakeNor,0x2004,boot.Length);
        byte[] rw=Encoding.ASCII.GetBytes("DI-RS1_RW_1.00"); Array.Copy(rw,0,fakeNor,0x10008,rw.Length);
        fakeNor[0x10030]=0x18; fakeNor[0x10031]=1; fakeNor[0x10032]=0xe7; fakeNor[0x10033]=0xfe;
        fakeNor[0x2000]=fakeNor[0x2001]=0; fakeNor[0x2002]=fakeNor[0x2003]=255;
        int sum=0; for(int i=0;i<0x8000;i++) sum=(sum+fakeNor[i])&65535;
        fakeNor[0x2000]=(byte)(sum>>8); fakeNor[0x2001]=(byte)sum;
        fakeNor[0x2002]=(byte)((sum^65535)>>8); fakeNor[0x2003]=(byte)(sum^65535);
    }
    static int CvGetCommandEX(int port,IntPtr command,int length,IntPtr response,int capacity) {
        readCount++;
        byte[] bytes=new byte[length]; Marshal.Copy(command,bytes,0,length);
        string text=Encoding.ASCII.GetString(bytes);
        Require(length==40 && text.StartsWith("\x1bP"+"MNT_RDMEMORYDUMP32    00000008"),"non-read memory command sent");
        uint address=uint.Parse(text.Substring(32),System.Globalization.NumberStyles.HexNumber);
        if(address>=0x1c046800 && address<0x1c046820 || address>=0x1c046400 && address<0x1c046440) {
            byte[] wordRam=new byte[]{255,255,255,255};
            if(phase==2 && destination==VgTarget && address>=0x1c046800)
                Array.Copy(VgMarker,(int)(address-0x1c046800),wordRam,0,4);
            byte[] hexRam=Encoding.ASCII.GetBytes(BitConverter.ToString(wordRam).Replace("-",""));
            Marshal.Copy(hexRam,0,response,8);return 8;
        }
        Require(address>=0x20000000 && address<=0x201ffffc && address%4==0,"invalid NOR address");
        if(invalidNorResponse || (failReadAfter>0 && readCount>failReadAfter)) return 0;
        int offset=(int)(address-0x20000000);
        byte[] word=new byte[4]; Array.Copy(fakeNor,offset,word,0,4);
        if(wrongDiBoot && address==0x20002004) word[0]=(byte)'X';
        byte[] hex=Encoding.ASCII.GetBytes(BitConverter.ToString(word).Replace("-",""));
        Marshal.Copy(hex,0,response,hex.Length); return 8;
    }
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
                using(var guard=new Mutex(false,UsbMutexName)) {
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
        string diFile=Path.Combine(root,"DI-RS1_0102.bin"); byte[] diPayload=File.ReadAllBytes(diFile);
        string vgFile=Path.Combine(root,"VG-RX1HS-02.21.bin");
        PrepareFakeNor(); Reset("DS-RX1 02.21",VgTarget,File.ReadAllBytes(vgFile));
        Flash(initialVersion,actualSerial,VgTarget,vgFile);passed++;
        Require(VgProduction(),"production marker missing");
        Reset("DS-RX1 02.21",VgTarget,File.ReadAllBytes(vgFile));wrongDiBoot=true;
        Reject(()=>Flash(initialVersion,actualSerial,VgTarget,vgFile),0,"original DI bootloader");passed++;
        Reset("DS-RX1 02.21","02.21",File.ReadAllBytes(Path.Combine(root,"02.21.bin")));
        Flash(initialVersion,actualSerial,"02.21",Path.Combine(root,"02.21.bin"));passed++;
        PrepareFakeNor(); Reset("DS-RX1 02.21",DiTarget,diPayload);
        Flash(initialVersion,actualSerial,DiTarget,diFile);
        Require(calls.Count==2 && calls[0]=="enter" && calls[1]=="write","DI sequence failed");
        Require(readCount==24,"DI restoration must only read boot and recovery identification, without a full backup"); passed++;
        Reset("DS-RX1 02.21",DiTarget,diPayload); wrongDiBoot=true;
        Reject(()=>Flash(initialVersion,actualSerial,DiTarget,diFile),0,"original DI bootloader");
        Require(calls.Count==0,"wrong boot entered update mode"); passed++;
        Reset("DS-RX1 02.21",DiTarget,diPayload); invalidNorResponse=true;
        Reject(()=>Flash(initialVersion,actualSerial,DiTarget,diFile),0,"NOR read failed");
        Require(calls.Count==0,"failed boot read entered update mode"); passed++;
        Reset("DS-RX1 02.21",DiTarget,diPayload); failReadAfter=12;
        Reject(()=>Flash(initialVersion,actualSerial,DiTarget,diFile),0,"NOR read failed");
        Require(calls.Count==0,"interrupted boot read entered update mode"); passed++;
        Reset("DI-RS1 01.02",DiTarget,diPayload);
        Reject(()=>Flash(initialVersion,actualSerial,DiTarget,diFile),0,"transition"); passed++;
        Reset("DS-RX1 02.21",DiTarget,diPayload); wrongFinalSerial=true;
        Reject(()=>Flash(initialVersion,actualSerial,DiTarget,diFile),1,"serial number"); passed++;
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
