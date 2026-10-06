using System;
using System.Text;
using System.Globalization;
using System.Runtime.InteropServices;

static partial class PrinterBridge {
    const string DiTarget="DI-RS1 01.02";
    const string DiHash="7E4A39F68791A670487B9116A92AD6A4E2D1AE938FCF4AF5A3E2E747331AAD8A";

    static byte[] ReadNor(uint start,int length) {
        bool editionRead=(start==0x1c046800 && length==32) || (start==0x1c046400 && length==64);
        if(!editionRead && (start<0x20000000 || (ulong)start+(ulong)length>0x20200000 || start%4!=0 || length<=0 || length%4!=0))
            throw new Exception("Invalid NOR read range");
        IntPtr cmd=Marshal.AllocHGlobal(40),reply=Marshal.AllocHGlobal(4096);
        try {
            byte[] data=new byte[length],raw=new byte[8];
            for(int offset=0;offset<length;offset+=4) {
                string packet="\x1bP"+"MNT_RD"+"MEMORYDUMP32".PadRight(16)+"00000008"+(start+(uint)offset).ToString("X8");
                Marshal.Copy(Encoding.ASCII.GetBytes(packet),0,cmd,40);
                if(CvGetCommandEX(0,cmd,40,reply,4096)!=8) throw new Exception("NOR read failed; no firmware transferred.");
                Marshal.Copy(reply,raw,0,8);
                foreach(byte b in raw) if(!(b>=48&&b<=57)&&!(b>=65&&b<=70)&&!(b>=97&&b<=102))
                    throw new Exception("Invalid NOR response; no firmware transferred.");
                uint word=uint.Parse(Encoding.ASCII.GetString(raw),NumberStyles.AllowHexSpecifier,CultureInfo.InvariantCulture);
                for(int j=0;j<4;j++) data[offset+j]=(byte)(word>>(24-8*j));
            }
            return data;
        } finally { Marshal.FreeHGlobal(cmd); Marshal.FreeHGlobal(reply); }
    }
    static void RequireDiBoot() {
        byte[] boot=ReadNor(0x20002000,32), recovery=ReadNor(0x20010000,64);
        if(Encoding.ASCII.GetString(boot,4,"DIRS1_BOOT 1.00".Length)!="DIRS1_BOOT 1.00" ||
           Encoding.ASCII.GetString(recovery,8,"DI-RS1_RW_1.00".Length)!="DI-RS1_RW_1.00" ||
           BitConverter.ToString(recovery,48,4)!="18-01-E7-FE")
            throw new Exception("DI restoration is only supported on converted DI-RS1 printers with the original DI bootloader. No update mode requested.");
    }
    static void CheckDiRestore() {
        int[] models=Enumerate();
        if(models.Length!=1 || models[0]!=5) throw new Exception("Connect one converted DI-RS1 with supported DNP firmware");
        string firmware=Read(0,CvGetVersion);
        if(!firmware.StartsWith("DS-RX1 ") ||
           Array.IndexOf(Versions,firmware.Substring(7))<0 || !Allowed(CvGetStatus(0)))
            throw new Exception("Connect one converted DI-RS1 with supported DNP firmware");
        RequireDiBoot();
        Emit("Original DI bootloader confirmed. Read-only compatibility check passed; no update mode requested.");
    }
}
