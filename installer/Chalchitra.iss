; ==================================================================
;  Chalchitra — Inno Setup Script
;  Compile with: iscc installer\Chalchitra.iss
; ==================================================================

#define MyAppName        "Chalchitra"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "AirSilo"
#define MyAppURL         "https://airsilo.space"
#define MyAppExeName     "Chalchitra.exe"
#define SourceDir        "..\dist\Chalchitra"

[Setup]
AppId={{8C4F7B2E-5A1D-4F8E-9B3C-2D6E7A9F1C4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; --- Install location (per-user, no admin prompt) ---
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; --- Output ---
OutputDir=..\dist
OutputBaseFilename=Chalchitra-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; --- Wizard appearance ---
WizardStyle=modern dark
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardImageFile=wizard-large.bmp
WizardSmallImageFile=wizard-small.bmp
WizardImageStretch=no
DisableWelcomePage=no
DisableReadyPage=no
DisableDirPage=no
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "fileassoc";    Description: "Add Chalchitra to ""Open with"" for video files"; GroupDescription: "Integration:"
Name: "contextmenu";  Description: "Add ""Play with Chalchitra"" to the right-click menu"; GroupDescription: "Integration:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";     Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; ==================================================================
;  Registry — file associations
; ==================================================================

[Registry]
; --- ProgID ---
Root: HKA; Subkey: "Software\Classes\Chalchitra.Video"; ValueType: string; ValueName: ""; ValueData: "Chalchitra Video File"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\Chalchitra.Video\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\Chalchitra.Video\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc

; --- "Open with" registration for each extension ---
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids";ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids";   ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithProgids"; ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithProgids"; ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.ogv\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\.3gp\OpenWithProgids";  ValueType: string; ValueName: "Chalchitra.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: fileassoc

; --- "Play with Chalchitra" right-click entry for each extension ---
#define CtxRoot "Software\Classes\SystemFileAssociations"

Root: HKA; Subkey: "{#CtxRoot}\.mp4\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mp4\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mp4\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.mkv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mkv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mkv\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.avi\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.avi\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.avi\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.mov\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mov\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.mov\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.webm\shell\PlayWithChalchitra";    ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.webm\shell\PlayWithChalchitra";    ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.webm\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.flv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.flv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.flv\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.wmv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.wmv\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.wmv\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

Root: HKA; Subkey: "{#CtxRoot}\.m4v\shell\PlayWithChalchitra";     ValueType: string; ValueName: "";        ValueData: "Play with Chalchitra"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.m4v\shell\PlayWithChalchitra";     ValueType: string; ValueName: "Icon";    ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKA; Subkey: "{#CtxRoot}\.m4v\shell\PlayWithChalchitra\command"; ValueType: string; ValueName: "";  ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Chalchitra now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel1.Caption := 'Welcome to the Chalchitra Setup Wizard';
  WizardForm.WelcomeLabel2.Caption :=
    'This will install Chalchitra, a minimal, fully offline media player ' +
    'for Windows.' + #13#10 + #13#10 +
    'Chalchitra plays almost every video format, never connects to the ' +
    'internet, and keeps all of your data on your own machine.' + #13#10 + #13#10 +
    'Click Next to continue, or Cancel to exit.';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption :=
      'Chalchitra has been installed on your computer.' + #13#10 + #13#10 +
      'Click Finish to close this wizard.';
end;