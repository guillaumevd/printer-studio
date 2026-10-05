using System;
using System.Runtime.InteropServices;

static partial class PrinterBridge {
    delegate int Getter(int port, ref string value);
    static string Read(int port, Getter get) {
        string value = new string('\0', 512);
        if (get(port, ref value) < 0) return "";
        int end = value.IndexOf('\0');
        return (end >= 0 ? value.Substring(0, end) : value).Trim();
    }
    static int[] Enumerate(bool allowUnavailable=false) {
        IntPtr data = Marshal.AllocHGlobal(256);
        try {
            for (int i=0; i<256; i++) Marshal.WriteByte(data, i, 0);
            int size=256, count=GetPrinterPortNum(data, ref size);
            if (count < 0 && allowUnavailable) return new int[0];
            if (count < 0 || count > 128) throw new Exception("USB enumeration failed");
            int[] models = new int[count];
            for (int i=0; i<count; i++) models[i]=Marshal.ReadByte(data, i*2);
            return models;
        } finally { Marshal.FreeHGlobal(data); }
    }
}
