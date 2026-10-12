; Inno Setup script for GTrans
; Invoked from the workflow as:
;   ISCC.exe /DMyAppVersion=<version> /DMySourcePath=<raw flet build output> /DMyRepoRoot=<repo root> windows.iss

#define MyAppName        "GTrans"
#define MyAppPublisher   "osamalzabidi"
#define MyAppURL         "https://github.com/osamalzabidi/gtrans"
#define MyAppExeName     "gtrans.exe"

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#ifndef MySourcePath
  #error MySourcePath must be defined via /DMySourcePath=...
#endif

#ifndef MyRepoRoot
  ; Fallback for local testing: assume .iss lives at .github\installer\
  #define MyRepoRoot "..\.."
#endif

[Setup]
AppId={{82fc94c6-080d-4bfe-86bd-f9d6e3f4594e}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#MyRepoRoot}\dist
OutputBaseFilename=GTrans-{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; Absolute path so ISCC doesn't look in .github\installer\src\...
SetupIconFile={#MyRepoRoot}\src\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MySourcePath}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";       Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent