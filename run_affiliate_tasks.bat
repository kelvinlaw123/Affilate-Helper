@echo off
setlocal enabledelayedexpansion

cd /d "path\to\your\Repo\Affilate Helper"
e:

:: ==== CONFIG ====
set PYTHON=python
set BASE_DIR=path\to\your\Repo\Affilate Helper
set LOG_DIR=%BASE_DIR%\Local Run\logs
set OUTPUT_LOG=%BASE_DIR%\Local Run\log.txt
set GIT_SCRIPT=%BASE_DIR%\proxy_tools\GitScraping.py
set CLICKER_SCRIPT=%BASE_DIR%\AffClicker_w_Aiohttp.py

:: Create log dir if not exists
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Get timestamp
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TIMESTAMP=%%a
set GIT_LOG=%LOG_DIR%\git_%TIMESTAMP%.log
set CLICKER_LOG=%LOG_DIR%\clicker_%TIMESTAMP%.log
set COMBINED_LOG=%LOG_DIR%\run_%TIMESTAMP%.log

:: ==== START RUN ====
echo === Run started at %DATE% %TIME% === > "%COMBINED_LOG%"
echo Running GitScraping.py...
%PYTHON% "%GIT_SCRIPT%" > "%GIT_LOG%" 2>&1
type "%GIT_LOG%" >> "%COMBINED_LOG%"

echo Running AffClicker_w_Aiohttp.py...
%PYTHON% "%CLICKER_SCRIPT%" > "%CLICKER_LOG%" 2>&1
type "%CLICKER_LOG%" >> "%COMBINED_LOG%"

echo === Run ended at %DATE% %TIME% === >> "%COMBINED_LOG%"

:: ==== PARSE COMBINED LOG ====
pushd "%LOG_DIR%"
echo [✓] Latest log file: run_%TIMESTAMP%.log
echo -----------------------------------
findstr /i /c:"Saved" /c:"working proxies" "run_%TIMESTAMP%.log"
echo -----------------------------------

:: Save to global log.txt
echo === %DATE% %TIME% === >> "%OUTPUT_LOG%"
findstr /i /c:"Saved" /c:"working proxies" "run_%TIMESTAMP%.log" >> "%OUTPUT_LOG%"
echo. >> "%OUTPUT_LOG%"
popd

endlocal
pause
