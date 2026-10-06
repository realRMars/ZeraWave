Option Explicit
Dim shell, fs, root, python, entry
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
entry = root & "\app\visuals\studio_workspace.pyw"
If Not fs.FileExists(python) Then
  MsgBox "ZeraWave's existing Python environment was not found: " & python & vbCrLf & "Use the documented diagnostic development entry point.", vbCritical, "ZeraWave Studio"
  WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run """" & python & """ -B -X utf8 """ & entry & """", 0, False
