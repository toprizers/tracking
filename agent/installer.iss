[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=Employee Monitor
AppVersion=1.0
AppPublisher=Your Company
DefaultDirName={autopf}\EmployeeMonitor
DefaultGroupName=Employee Monitor
OutputDir=..\installer_output
OutputBaseFilename=EmployeeMonitor_Setup_1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\MonitorAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Employee Monitor"; Filename: "{app}\MonitorAgent.exe"
Name: "{group}\Uninstall Employee Monitor"; Filename: "{uninstallexe}"
Name: "{commonstartup}\EmployeeMonitor"; Filename: "{app}\MonitorAgent.exe"

[Run]
Filename: "{app}\MonitorAgent.exe"; Parameters: "--install-autostart"; StatusMsg: "Installing auto-start..."; Flags: runhidden
Filename: "{app}\MonitorAgent.exe"; Description: "Start monitoring now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\screenshots"
Type: filesandordirs; Name: "{app}\agent.log"
