# DNP VG-RX1HS 2.21

The VG edition adds support for DNP, DI Support and Citizen CY-02 media. The owner
confirmed printing with all three on the project's converted DI-RS1. This is a
custom edition, not an official DNP firmware release. Other printers, formats
and media lots have not all been tested.

In Firmware, select **VG-RX1HS · 2.21**. Lower supported versions upgrade through
the stock DNP sequence before the VG installation. The original DI bootloader
is checked before VG transfer; this image is not provided for standard DNP
printers with a different bootloader. Normal identity/status/hash checks apply.

Printer Studio automatically displays **DNP VG-RX1HS** from the firmware's fixed
edition marker. The firmware continues to report **DS-RX1 02.21** to existing
drivers and vendor tools. Windows hardware identification depends on the model
name, and software may use its own model-name table. Therefore Hot Folder may
continue to display **RX1HS**; firmware alone cannot guarantee a custom name
there. No driver, USB identifier, Windows queue or Hot Folder DLL is changed.

The original DNP versions remain separate and use their original media policy.
Select **02.21 / DNP MEDIA ONLY** to replace VG with stock DNP 2.21, even though
the numeric version is unchanged. DI/Citizen acceptance is then removed.

The production image contains the tested media logic and a constant name marker.
It contains no temporary UID snapshots, tag-specific diagnostic exceptions or
extra RFID write commands. The first brand-identification check is relaxed
after both existing tables fail; other compatible readable media may also pass.
Subsequent metadata and format checks remain in place. This is not a recovered
Citizen secret authentication table.
