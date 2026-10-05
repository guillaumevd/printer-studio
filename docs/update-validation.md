# Application update validation

Validated on Windows x64 on 2026-10-05 for release **1.4.4**.

- 24 automated tests passed, covering release discovery, manifest validation, download integrity, cancellation, offline startup, splash API exposure and installer helper environment restoration.
- Packaged desktop self-tests passed: frameless 400 × 500 logical-pixel splash, no overflow, English interface, window icon and maximized workspace with the native title bar. Fullscreen remains disabled.
- A real installed **1.4.3 → 1.4.4** update passed against this repository's stable GitHub Release. The harness used the splash install button, downloaded the installer, verified SHA-256, closed the old application, completed silent installation and automatically started the new executable.
- The restarted executable reported version 1.4.4 and passed its isolated desktop self-test. Its hash matched the release build.
- The update integration harness used a simulated printer throughout. No USB commands were sent by that test.

A clean Windows VM without WebView2 was not tested; the installer includes Microsoft's signed runtime bootstrapper. Executables are not code-signed.

## Interface refinement in 1.4.5

The splash initializes hidden, completes DPI sizing and centering, then becomes visible. Both source and packaged desktop tests confirmed that its first observed visible position was centered, with no native title bar. The main workspace remains maximized.

The green splash halo, decorative USB symbol, overview eyebrow and local-application sidebar block were removed. The sidebar now shows the commercial-use permission notice and contact details requested by the application owner. The 24 automated tests passed before packaging.
