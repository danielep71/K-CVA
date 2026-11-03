@echo off
setlocal EnableExtensions
rem Double-click to record an Excel run of the checked-out commit:
rem tools\Record-KCVA-ExcelRun.ps1 builds a workbook, compiles and runs the
rem example suite, exports the modules, writes the evidence folder under
rem test-results\ and checks it with tools\check_excel_run.py.
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"
set "SCRIPT=%~dp0Record-KCVA-ExcelRun.ps1"
if not exist "%SCRIPT%" (
    echo ERROR: PowerShell script not found:
    echo   %SCRIPT%
    pause
    exit /b 1
)
echo K-CVA Excel run
echo Repository: %CD%
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo PASS: the run is recorded and consistent with the commit.
    echo Send the content of check.txt, shown above.
) else (
    echo NOT PASSED: exit code %RC%. Send the output above as it is.
)
echo.
pause
exit /b %RC%
