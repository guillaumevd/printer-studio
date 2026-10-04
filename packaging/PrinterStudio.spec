# Build from printer-studio with: python -m PyInstaller packaging/PrinterStudio.spec
from pathlib import Path
root = Path(SPECPATH).parent
a = Analysis(
    [str(root / 'desktop.pyw')], pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'web'), 'web'), (str(root / 'firmware'), 'firmware'),
           (str(root / 'native' / 'PrinterBridge.exe'), 'native'),
           (str(root / 'native' / 'cspstat64.dll'), 'native'),
           (str(root / 'native' / 'checksums.json'), 'native')],
    hiddenimports=['webview.platforms.winforms', 'webview.platforms.edgechromium'],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter', 'gi'],
    hookspath=[], runtime_hooks=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Printer Studio',
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / 'web/assets/printer.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Printer Studio')
