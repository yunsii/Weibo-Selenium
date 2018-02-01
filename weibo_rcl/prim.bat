@echo off
set "root_path=c:\prim\"
set "firefoxconf=%root_path%firefoxconf.selenium"
echo 目标文件夹 %firefoxconf%
if exist %firefoxconf% (echo %firefoxconf%已存在
) else (
md %firefoxconf%
echo 新建%firefoxconf%
)
set "pwd=%~dp0"
::echo pwd is
::echo %pwd%
::echo path is
::echo %path%
set "selenium=%pwd%firefoxconf.selenium"
echo 源文件夹 %selenium%
Xcopy "%selenium%" "%firefoxconf%" /s /e /d /y
echo 添加火狐浏览器驱动到系统环境变量

if not exist sys_path_bak.txt (call sys_path_bak.bat)

set /p path_=<sys_path_bak.txt
echo 环境变量sys_path_bak: %path_%

::set "new_path=%path_%;%pwd%"
echo 修改后的path: %new_path%
rem 合并用户path和系统path
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v path /d "%path_%
::reg add "HKCU\Environment" /v path /d "%new_path%
setx "Path" "%pwd%
echo 修改后的环境变量:
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v path
reg query "HKCU\Environment" /v path
pause