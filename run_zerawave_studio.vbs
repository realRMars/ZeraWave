Option Explicit
Dim shell, fs, environmentRoot, baseline, python, entry
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")

' All accepted Studio progress: published checkpoint plus approved audio repair.
environmentRoot = fs.GetParentFolderName(WScript.ScriptFullName)
baseline = environmentRoot
python = environmentRoot & "\.venv\Scripts\pythonw.exe"
entry = baseline & "\app\visuals\studio_qt.pyw"

If Not fs.FileExists(python) Then
  MsgBox "ZeraWave's Python environment was not found: " & python, vbCritical, "ZeraphinaX Studio"
  WScript.Quit 1
End If
If Not fs.FileExists(entry) Then
  MsgBox "The approved Studio baseline was not found: " & baseline, vbCritical, "ZeraphinaX Studio"
  WScript.Quit 1
End If

shell.CurrentDirectory = baseline
shell.Run """" & python & """ -B -X utf8 """ & entry & """", 0, False
