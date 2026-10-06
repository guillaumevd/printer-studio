# Original DI firmware restoration — 1.6.1

On 6 October 2026, the project's converted DI-RS1 was successfully restored
from DNP 2.21 to DI-RS1 01.02. It restarted ready with its serial, CWD, counters
and media information unchanged. The owner subsequently confirmed that printing
worked. Other supported DNP source versions have not been physically tested
for DI restoration.

The original DI firmware was recovered using `MNT_RD / MEMORYDUMP32`.
Two independent 2 MiB reads matched byte for byte. Only the 353,840-byte main
application container at physical offset `0x80000` forms the restoration payload.
The donor's settings sectors, serial number and full flash image are excluded.
Container checks and an independent S-record decoder pass; the same encoder
reproduces the official DNP 2.21 file byte for byte. Python and C# lock the
Windows payload by size and SHA-256.

Before update mode, the bridge verifies the payload, printer model, source
firmware, serial and status. It reads 96 bytes to check `DIRS1_BOOT 1.00`,
`DI-RS1_RW_1.00` and the recovery identifier. Factory DNP printers without
that DI bootloader are rejected. The interface keeps the normal firmware
change confirmation.

Version 1.6.1 removes the experimental status and automatic full backup.
Existing backups are preserved. The writer uses the same vendor library and
DI recovery transport, then verifies DI firmware/model, serial and CWD after
restart. No CWD, RFID, calibration, serial or counter setter is imported.

The successful supervised hardware restoration reused a previously verified
backup with fresh identity and NOR checkpoint checks. Version 1.6.1 retains
the same payload and writer. A native regression verifies that only the 24
boot/recovery words are read, without a full backup. Further isolated tests
cover wrong bootloaders, failed reads, identity mismatches and exact transfers.
API and desktop simulations exercise normal confirmation and restoration.
They do not perform additional physical firmware writes.

The DI binary is excluded from Git and included in local distributions.
Private backups and printer logs stay on the PC.
