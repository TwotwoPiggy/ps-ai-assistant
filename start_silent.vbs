' ============================================
'  PS AI Assistant - 静默启动器
'  双击此文件启动服务, 完全不显示 cmd 窗口,
'  仅在系统托盘显示图标 (需先安装托盘依赖).
'
'  原理: pythonw.exe 本身无控制台, 启动后无窗口;
'        此 VBS 仅负责找到 pythonw 并拉起 launcher.py.
'
'  使用前请确保已安装: pip install -r requirements-launcher.txt
'  退出服务: 右键托盘图标 -> 退出
' ============================================

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' ---- 探测 pythonw.exe 完整路径 ----
' 候选顺序: venv pythonw > venv python > 系统 pythonw > 系统 python
Dim candidates(3)
candidates(0) = scriptDir & "\.venv\Scripts\pythonw.exe"
candidates(1) = scriptDir & "\venv\Scripts\pythonw.exe"
candidates(2) = shell.ExpandEnvironmentStrings("%LocalAppData%\Programs\Python\Python314\pythonw.exe")

Dim pythonExe
pythonExe = ""
For Each c In candidates
    If fso.FileExists(c) Then
        pythonExe = c
        Exit For
    End If
Next

' 系统级回退: 直接用 pythonw (依赖 PATH)
If pythonExe = "" Then pythonExe = "pythonw"

' ---- 设置环境变量 ----
Set env = shell.Environment("Process")
env.Item("PYTHONUNBUFFERED") = "1"
env.Item("PYTHONUTF8") = "1"
env.Item("PYTHONIOENCODING") = "utf-8"
env.Item("PSAI_SILENT") = "1"

' ---- 启动 (隐藏窗口 0, 不等待 False) ----
shell.CurrentDirectory = scriptDir
shell.Run Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & scriptDir & "\launcher.py" & Chr(34), 0, False
