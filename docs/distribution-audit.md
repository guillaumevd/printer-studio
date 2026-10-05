# Distribution and conversion audit — 1.5.0

Validated on Windows x64 on 2026-10-05.

## Distribution contents

The final installer was unpacked independently and compared with the extracted portable ZIP. Both contained **118 identical application files**, including the integrity manifest. All **117 manifest entries** passed SHA-256 and size verification.

The packages include Python 3.12, WebView2/.NET Python bindings and loaders, the x64 USB bridge, the vendor USB DLL and native checksums, all four firmware images, the HTML/CSS/JavaScript components and artwork. Both now include Microsoft's signed WebView2 bootstrapper; the portable folder also includes `Install WebView2.cmd`.

Python is not required on the destination machine. The printer's Windows USB driver is required separately. WebView2 must be installed; the installer handles it automatically and the portable helper installs it when needed. The bootstrapper needs Internet. The USB DLL imports only Windows SETUPAPI, KERNEL32 and ADVAPI32. The native bridge uses Windows .NET Framework 4.

## Historical conversion comparison

The four firmware streams match the successful August 2026 payloads byte for byte, including their historical padding:

| DNP version | Payload bytes | SHA-256 |
| --- | ---: | --- |
| 02.04 | 2,064,464 | `95115c6e13e2121e2640ce6df214926bb3fc94eef2549d6b4890062b6420772a` |
| 02.07 | 2,064,464 | `beb2799f45d90f7aed1070160cf4399542e3df24fdecb6a000e3a84e91d029fc` |
| 02.10 | 2,064,464 | `464ed3eb44fae83633c00dd28455dcdf04a67aa7d99393f351d7bdad726755a7` |
| 02.21 | 1,609,144 | `840f80a230db68c670dc7682fb83554d57a3add8be8e2216d3da26600edebb86` |

The supported original identity is DI-RS1 01.02, model 91. Conversion starts with 02.04 and proceeds through 02.07, 02.10 and 02.21, verifying identity, status, firmware and serial after each step. The native flow enters update mode, waits for model 91 / DI-RS1_RW_1.00 / status 0x00100001, sends the unchanged verified stream through SetFirmwDataWrite, and verifies the DNP result. Temporary absence during USB reconnection is tolerated; no automatic retry of a firmware write is performed.

The current vendor DLL is the same version documented in the original DI read-only probe and subsequent historical DNP steps. The first historical 02.04 sender used an older DLL build with the same firmware-write API. This application reproduces the verified stream and protocol, rather than reusing that old sender binary.

No CWD, RFID, identity, calibration, maintenance or counter write export is declared by the bridge. Unsupported original firmware versions and bootloader-only identities cannot initiate a conversion.

## Tests and limits

- 24 Python tests passed, including complete conversion planning, serialized access, identity/status checks, failed verification, interrupted-operation blocking and HTTP security.
- 17 native tests passed. They compile the actual bridge workflow against a fake USB API, covering DI information reads, the firmware transitions, exact transmitted bytes, temporary absence, bad identities/statuses/bootloaders, corrupt payloads, failed writes and serial mismatch after restart. They load no vendor DLL and access no USB hardware.
- Desktop tests passed for executables extracted independently from the installer and portable ZIP, with Python removed from PATH, Python environment variables cleared and a different working directory. The tests verify bundle integrity, original DI information, the four-step simulated conversion, DNP downgrade, splash positioning and maximized workspace.
- The portable integrity CLI passed separately without opening a window or accessing USB.

The printer available for this audit is already converted. A new physical DI-to-DNP conversion was **not** performed during this audit. Hardware results in the historical reports remain the evidence for that initial conversion. A clean Windows VM without WebView2 was not available. The executable is not code-signed.

## Public repository checks

Tracked files and Git history were checked for GitHub access tokens, private keys, embedded credentials and real printer serials. No matches were found. Printer logs, conversation archives, local settings, caches and build tools are excluded. The owner's name and phone number are intentionally public, as requested. Release archives contain only application resources; the shared vendor-resource archive contains only the four firmware images and USB DLL.

The HTTP server binds to loopback, checks host and mutation origin, requires a session token for changes and renders printer/log text using textContent. Application-update downloads are restricted to this repository's release assets and checked for size and SHA-256. Hardware and clean-VM validation limits are listed above.
