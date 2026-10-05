# Changelog

## 1.5.0

- Separate firmware, printer transports, desktop, HTTP, validation and frontend components.
- Add native protocol tests using the actual bridge workflow with a fake USB API.
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

