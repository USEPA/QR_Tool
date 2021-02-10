; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{B5515227-FBDB-4D37-84BE-771B6B3FBFC4}
AppName=QR-Toolbox
AppVersion=1.3
;AppVerName=QR-Toolbox 1.3
AppPublisher=EPA ORD
DefaultDirName={autopf}\QR-Toolbox
DisableProgramGroupPage=yes
InfoBeforeFile=C:\Users\mkarimi\PycharmProjects\QR_Tool\dist\QR-Toolbox\Documentation\installer.txt
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=QR-Toolbox-Installer-v1.3
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\mkarimi\PycharmProjects\QR_Tool\dist\QR-Toolbox\QR-Toolbox.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\mkarimi\PycharmProjects\QR_Tool\dist\QR-Toolbox\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\QR-Toolbox"; Filename: "{app}\QR-Toolbox.exe"
Name: "{autodesktop}\QR-Toolbox"; Filename: "{app}\QR-Toolbox.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\QR-Toolbox.exe"; Description: "{cm:LaunchProgram,QR-Toolbox}"; Flags: nowait postinstall skipifsilent

