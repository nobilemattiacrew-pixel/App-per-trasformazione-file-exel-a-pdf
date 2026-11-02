#define AppName "Fogli in PDF"
#define AppVersion "1.0.0"
#define AppPublisher "Fogli in PDF"

[Setup]
AppId={{E4762A21-CE95-4DA8-989B-61B5DC542001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Fogli in PDF
DefaultGroupName={#AppName}
OutputDir=..\..\dist\installer
OutputBaseFilename=FogliInPDF-Setup-Windows
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\FogliInPDF.exe

[Files]
Source: "..\..\dist\FogliInPDF\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Fogli in PDF"; Filename: "{app}\FogliInPDF.exe"
Name: "{autodesktop}\Fogli in PDF"; Filename: "{app}\FogliInPDF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti aggiuntivi:"