using System;
using System.Collections.Generic;

static partial class PrinterBridge {
    static void Probe() {
        var list = new List<object>(); int[] models=Enumerate();
        for (int i=0;i<models.Length;i++) {
            if (models[i]!=5 && models[i]!=91) {
                list.Add(new { model=models[i], firmware="Unsupported model", serial="", status="unknown" });
                continue;
            }
            int status=CvGetStatus(i); string firmware=Read(i,CvGetVersion);
            bool normal=firmware.StartsWith("DS-RX1 ") || firmware.StartsWith("DI-RS1 ");
            string edition=normal && Allowed(status)?MediaEdition(firmware):"unknown";
            list.Add(new { model=models[i], firmware=firmware, status="0x"+status.ToString("X8"),
                edition=edition, display_name=edition==VgTarget?"DNP VG-RX1HS":models[i]==91?"DI-RS1":"DNP DS-RX1",
                serial=normal ? Read(i,CvGetSerialNo) : "", cwd=normal ? Read(i,CvGetColorDataVersion) : "",
                counter=normal ? CvGetCounterL(i) : -1, media=normal ? CvGetMediaCounter(i) : -1,
                capacity=normal ? GetInitialMediaCount(i) : -1 });
        }
        Console.WriteLine(json.Serialize(list));
    }
}
