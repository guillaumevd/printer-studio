using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

static partial class PrinterBridge {
    static readonly string[] Versions = {"02.04", "02.07", "02.10", "02.21"};
    static readonly string[] Hashes = {
        "95115C6E13E2121E2640CE6DF214926BB3FC94EEF2549D6B4890062B6420772A",
        "BEB2799F45D90F7AED1070160CF4399542E3DF24FDECB6A000E3A84E91D029FC",
        "464ED3EB44FAE83633C00DD28455DCDF04A67AA7D99393F351D7BDAD726755A7",
        "840F80A230DB68C670DC7682FB83554D57A3ADD8BE8E2216D3DA26600EDEBB86"};
    static void Flash(string source, string serial, string target, string path) {
        bool vg=target==VgTarget;
        int index=vg?3:Array.IndexOf(Versions,target);
        int sourceIndex=source.StartsWith("DS-RX1 ") ? Array.IndexOf(Versions,source.Substring(7)) : -1;
        bool diRestore=target==DiTarget && sourceIndex>=0;
        bool conversion=source=="DI-RS1 01.02" && index==0;
        bool dnpTransition=sourceIndex>=0 && (index==sourceIndex+1 || index<sourceIndex || index==3 && sourceIndex==3);
        if (!diRestore && (index<0 || !(conversion || dnpTransition)))
            throw new Exception("Unsupported firmware transition");
        byte[] payload=File.ReadAllBytes(path);
        using (SHA256 sha=SHA256.Create()) {
            if (BitConverter.ToString(sha.ComputeHash(payload)).Replace("-","")!=(diRestore?DiHash:vg?VgHash:Hashes[index]))
                throw new Exception("Firmware checksum mismatch");
        }
        if (payload.Length != (diRestore?1009156:vg?VgSize:index==3 ? 1609144 : 2064464)) throw new Exception("Invalid payload size");
        int[] models=Enumerate();
        if (models.Length!=1 || models[0]!=(conversion?91:5) || Read(0,CvGetVersion)!=source ||
            serial.Length==0 || Read(0,CvGetSerialNo)!=serial || !Allowed(CvGetStatus(0)))
            throw new Exception("Printer identity or status has changed");
        string originalCwd=diRestore || vg?Read(0,CvGetColorDataVersion):"";
        if(diRestore || vg) RequireDiBoot();
        Emit("Identity and checksum verified. Entering update mode.");
        if (CvSetFirmwUpdateMode(0)==0) throw new Exception("Update mode rejected");
        bool ready=false;
        for(int i=0;i<60;i++) {
            Delay(500); models=Enumerate(true);
            if(models.Length==1 && models[0]==91 && CvGetStatus(0)==0x100001 && Read(0,CvGetVersion)=="DI-RS1_RW_1.00") { ready=true; break; }
        }
        if(!ready) throw new Exception("Expected DI bootloader not detected. No firmware transferred.");
        Emit("DI bootloader confirmed. Transferring "+payload.Length+" bytes.");
        IntPtr buffer=Marshal.AllocHGlobal(payload.Length);
        try {
            Marshal.Copy(payload,0,buffer,payload.Length);
            if(SetFirmwDataWrite(0,buffer,payload.Length)==0) throw new Exception("USB transfer failed");
        } finally { Marshal.FreeHGlobal(buffer); }
        Emit("Transfer sent. Programming and restarting; keep the printer connected.");
        for(int i=0;i<300;i++) {
            Delay(1000); models=Enumerate(true);
            if(models.Length>1) throw new Exception("Multiple printers detected after transfer");
            if(models.Length!=1) continue;
            int status=CvGetStatus(0);
            if(status==0x100008 || status==0x100010) throw new Exception("Bootloader error: 0x"+status.ToString("X8"));
            string destination=diRestore?DiTarget:vg?"DS-RX1 02.21":"DS-RX1 "+target;
            if(models[0]==(diRestore?91:5) && Allowed(status) && Read(0,CvGetVersion)==destination) {
                if(Read(0,CvGetSerialNo)!=serial) throw new Exception("Unexpected serial number after restart");
                if((diRestore || vg) && Read(0,CvGetColorDataVersion)!=originalCwd) throw new Exception("CWD identity changed after transfer");
                if(vg && !VgProduction()) throw new Exception("VG-RX1HS firmware edition was not confirmed after restart");
                if(!diRestore && !vg && index==3 && MediaEdition(destination)!="stock") throw new Exception("Stock DNP firmware edition was not confirmed after restart");
                Emit("Firmware "+destination+" and serial number confirmed."); return;
            }
            if(i%10==0) Emit("Waiting for USB reconnection, status 0x"+status.ToString("X8"));
        }
        throw new Exception("Result unknown after 300 seconds. Manual inspection required.");
    }
}
