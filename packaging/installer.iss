#ifndef AppVersion
#define AppVersion "1.4.4"
#endif
[Setup]
AppId={{BD38D56E-23E5-4CDD-B945-C739E35830E7}
AppName=Printer Studio
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Printer Studio
DefaultGroupName=Printer Studio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\release
OutputBaseFilename=PrinterStudio-Setup-{#AppVersion}-x64
SetupIconFile=..\web\assets\printer.ico
UninstallDisplayIcon={app}\Printer Studio.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
AppMutex=Local\PrinterStudio.Running
CloseApplications=no
RestartApplications=no
InfoBeforeFile=INSTALL-NOTES.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\Printer Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "vendor\MicrosoftEdgeWebview2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{group}\Printer Studio"; Filename: "{app}\Printer Studio.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Printer Studio"; Filename: "{app}\Printer Studio.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\Printer Studio Demo"; Filename: "{app}\Printer Studio.exe"; Parameters: "--demo --port 8766"; WorkingDir: "{app}"

[Run]
Filename: "{app}\Printer Studio.exe"; Description: "Launch Printer Studio"; Flags: nowait postinstall skipifsilent

[Code]
function HasWebView2: Boolean;
var V: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V) and (V <> '') and (V <> '0.0.0.0'));
  if not Result then
    Result := (RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', V) and (V <> '') and (V <> '0.0.0.0'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not HasWebView2 then begin
    ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'Unable to start the Microsoft WebView2 installer.'
    else if not HasWebView2 then
      Result := 'WebView2 installation did not complete. Connect to the Internet, install Microsoft Edge WebView2 Runtime and run this installer again.';
  end;
end;
