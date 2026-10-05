using System;
using System.Text;
using System.Web.Script.Serialization;

static partial class PrinterBridge {
    static JavaScriptSerializer json = new JavaScriptSerializer();
    static void Emit(string message) { Console.WriteLine(json.Serialize(new { message=message })); }
    static bool Allowed(int status) { return status==0x10001 || status==0x10008 || status==0x10010 || status==0x20008; }
    static int Main(string[] args) {
        Console.OutputEncoding=new UTF8Encoding(false);
        try {
            if(args.Length==1 && args[0]=="probe") Probe();
            else if(args.Length==5 && args[0]=="flash") Flash(args[1],args[2],args[3],args[4]);
            else throw new Exception("Invalid arguments");
            return 0;
        } catch(Exception ex) { Emit(ex.Message); return 1; }
    }
}
