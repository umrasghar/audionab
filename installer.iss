; ============================================
;  AudioNab - Inno Setup Installer Script
; ============================================
;  Builds a production-grade Windows installer:
;  - Installs to Program Files
;  - Start Menu + Desktop shortcuts
;  - Registers in Add/Remove Programs
;  - Installs right-click context menu
;  - Clean uninstall (removes everything)
;
;  Requirements: Inno Setup 6+
;  Input: dist\AudioNab.exe (from build.bat)
;
;  Build: Open this file in Inno Setup Compiler
;         or run: iscc installer.iss
; ============================================

#define MyAppName "AudioNab"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "AudioNab"
#define MyAppURL "https://github.com/umrasghar/audionab"
#define MyAppExeName "AudioNab.exe"

[Setup]
AppId={{A8D7E3F1-B2C4-4D5E-9F6A-1B2C3D4E5F6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=AudioNab-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\icon.ico
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "Add ""Nab Audio"" to right-click context menu"; GroupDescription: "System Integration:"; Flags: checked
Name: "classicmenu"; Description: "Enable full right-click menu on Windows 11 (skip 'Show more options')"; GroupDescription: "System Integration:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Bundle app icons
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion
; Bundle FFmpeg if available
Source: "ffmpeg\ffmpeg.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ffmpeg\ffprobe.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; ── Context menu entries for all supported formats ──
; Video formats
Root: HKCR; Subkey: "SystemFileAssociations\.mp4\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mp4\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mp4\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.mkv\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mkv\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mkv\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.avi\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.avi\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.avi\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.mov\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mov\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mov\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.wmv\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wmv\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wmv\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.flv\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.flv\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.flv\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.webm\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.webm\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.webm\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.m4v\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4v\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4v\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.ts\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.ts\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.ts\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.mpg\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpg\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpg\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.mpeg\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpeg\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpeg\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.3gp\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.3gp\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.3gp\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.vob\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.vob\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.vob\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

; Audio formats
Root: HKCR; Subkey: "SystemFileAssociations\.m4a\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4a\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4a\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.flac\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.flac\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.flac\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.wav\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wav\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wav\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.ogg\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogg\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogg\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.wma\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wma\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.wma\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.aac\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.aac\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.aac\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

Root: HKCR; Subkey: "SystemFileAssociations\.opus\shell\AudioNab"; ValueType: string; ValueData: "Nab Audio"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.opus\shell\AudioNab"; ValueName: "Icon"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCR; Subkey: "SystemFileAssociations\.opus\shell\AudioNab\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" --convert ""%1"""; Tasks: contextmenu

; ── Win11 classic context menu (optional) ──
Root: HKCU; Subkey: "Software\Classes\CLSID\{{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"; ValueType: string; ValueData: ""; Flags: uninsdeletekey; Tasks: classicmenu

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\AudioNab"

[Code]
// Restart Explorer after install/uninstall to apply context menu changes
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Notify shell of changes
    Exec('cmd.exe', '/c echo. >nul', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
