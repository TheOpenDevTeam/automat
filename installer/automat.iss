; AUTOMAT installer — Inno Setup 6 script.
; Builds AUTOMAT-Setup-<version>.exe from the PyInstaller onedir output.
; Run from the repo root after `pyinstaller ... automat/main.py`:
;   ISCC.exe installer\automat.iss
; Version is intentionally hardcoded to match pyproject.toml.

#define AppVersion "1.0b1"

[Setup]
AppId={{E9CD11D7-BA99-4BC8-8D23-6FA83248065B}
AppName=AUTOMAT
AppVersion={#AppVersion}
AppVerName=AUTOMAT {#AppVersion}
AppPublisher=OpenDev
AppPublisherURL=https://github.com/TheOpenDevTeam/automat
AppSupportURL=https://github.com/TheOpenDevTeam/automat/issues
AppUpdatesURL=https://github.com/TheOpenDevTeam/automat/releases
DefaultDirName={autopf}\AUTOMAT
DefaultGroupName=AUTOMAT
LicenseFile=..\LICENSE
OutputDir=Output
OutputBaseFilename=AUTOMAT-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName=AUTOMAT {#AppVersion}
VersionInfoVersion=1.0.0.1
VersionInfoDescription=AUTOMAT — Task Automation Manager

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller onedir layout: AUTOMAT.exe + _internal\ tree.
Source: "..\dist\AUTOMAT\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AUTOMAT"; Filename: "{app}\AUTOMAT.exe"
Name: "{group}\{cm:UninstallProgram, AUTOMAT}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\AUTOMAT"; Filename: "{app}\AUTOMAT.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AUTOMAT.exe"; Description: "{cm:LaunchProgram, AUTOMAT}"; Flags: nowait postinstall skipifsilent
