using System;
using System.Text;

static partial class PrinterBridge {
    const string VgTarget="VG-02.21";
    const string VgHash="207264AEC62D21A373B51A16E45BA4C52214BC370B044C1DD1CEC92A98256A93";
    const int VgSize=1610056;
    static readonly byte[] VgMarker=Encoding.ASCII.GetBytes("DNP VG-RX1HS|02.21|MEDIA3|V1".PadRight(32,'\0'));
    static bool VgProduction() {
        return BitConverter.ToString(ReadNor(0x1c046800,32))==BitConverter.ToString(VgMarker);
    }
    static string MediaEdition(string firmware) {
        if(firmware!="DS-RX1 02.21") return "stock";
        try {
            if(VgProduction()) return VgTarget;
            // Recognize the user-tested predecessor with identical media logic.
            string shim=BitConverter.ToString(ReadNor(0x1c046400,64)).Replace("-","");
            if(shim=="D70A470B7408610E21188B02D208422B000952F4D10732108B05D2071F24E000D203422B0009D205422B00091C0427D41C03EC3C1C022FE01C022FD81C03EC2A") return VgTarget;
            return "stock";
        } catch { return "unknown"; }
    }
}
