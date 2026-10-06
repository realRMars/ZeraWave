Option Explicit
Dim shell, fs, root, python, entry
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
entry = root & "\app\visuals\studio_qt.pyw"
shell.CurrentDirectory = root
shell.Run """" & python & """ -B -X utf8 """ & entry & """", 0, False
