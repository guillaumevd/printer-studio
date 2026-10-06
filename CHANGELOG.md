# Changelog

## 1.8.0

- Keep printer information and firmware selection together in a full-height dashboard.
- Keep the activity log hidden until selected, with a running-operation indicator.
- Adapt card sizes and spacing to the available window height.

## 1.7.1

- Move original DI-RS1 1.02 into the shared firmware catalog and confirmation flow.
- Add illustrated media cards with brand badges and a three-brand gradient design for VG-RX1HS.
- Remove the separate DI restoration panel.

## 1.7.0

- Add the DNP VG-RX1HS 2.21 edition, with DNP, DI Support and Citizen CY-02 media tested by the owner on the converted DI-RS1.
- Identify the VG edition automatically and preserve DS-RX1 USB and protocol names for driver and Hot Folder compatibility.
- Keep stock DNP images separate; allow reinstalling stock 2.21 to remove VG media support.
- Include only production media logic and a fixed edition marker; no temporary RFID capture code.

## 1.6.1

- Validate DNP 2.21 to DI-RS1 01.02 restoration and subsequent printing on the project's converted printer.
- Remove the experimental badge and extra experimental confirmation.
- Remove the automatic full firmware backup before DI restoration.
- Retain firmware checksums, original DI boot/recovery checks and printer identity verification before and after transfer.

## 1.6.0

- Add experimental DI-RS1 01.02 restoration for converted DI printers with the original DI bootloader.
- Check boot/recovery by read-only USB memory commands and save a complete 2 MiB backup before programming.
- Verify DI model/firmware, serial and CWD after restoration; require a separate confirmation in the interface.
- Include the recovered application-only DI payload in local standalone packages, with fixed SHA-256 checks.
- Keep physical restoration explicitly unverified until tested on a converted printer.

## 1.5.0

- Separate firmware, printer transports, desktop, HTTP, validation and frontend components.
- Add native protocol tests using the actual bridge workflow with a fake USB API.
- Serialize native USB access across installations and command-line launches.
- Verify original DI detection and the complete four-step conversion in the desktop test.
- Tolerate temporary USB absence during recovery and restart polling.
- Add a complete distribution integrity manifest and offline verification command.
- Include the Microsoft WebView2 bootstrapper in the portable distribution.

## 1.4.5

- Prepare and center the splash while hidden, then reveal it at its final position.
- Remove the splash halo and decorative overview elements.
- Display the commercial-use permission notice and contact number in the sidebar.

## 1.4.4

- Add regression coverage for external helper startup and DLL environment restoration.

## 1.4.3

- Isolate the Windows installer helper from the bundled Python DLL environment.
- Verify installer checksums using .NET and retain helper diagnostics.

## 1.4.2

- Open the workspace maximized, retaining the title bar and Windows taskbar.
- Keep the frameless startup splash at 400 Ã— 500 logical pixels.

## 1.4.1

- Match VG-Timing's 400 Ã— 500 startup window without a native title bar.
- Keep the splash visible during printer detection and workspace initialization.
- Open the loaded workspace in fullscreen.
- Fix the splash API and prepare the packaged update integration harness.

## 1.4.0

- Add a dedicated startup screen with printer artwork and progress display.
- Check GitHub Releases for application updates and offer installation or skipping.
- Verify installer size and SHA-256, wait for application exit, install and restart.
- Continue offline if release checking fails.
- Keep application updates separate from printer firmware operations.

## 1.3.0

- Package Python, WebView2 bindings and USB resources into a Windows executable.
- Add a per-user installer and portable distribution.
- Verify the 02.21 to 02.10 downgrade on the project's printer.

