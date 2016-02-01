@echo off
set VENV=env
IF NOT EXIST "%VENV%\.done" (
    py.exe -2 -m virtualenv "%VENV%" && echo. > "%VENV%\.done"
)

call "%VENV%\Scripts\activate.bat"
setlocal
set "REQ=%~dp0\requirements.txt"
set "REQ_ENV=%VENV%\requirements.txt"
fc "%REQ%" "%REQ_ENV%" > nul 2>nul
IF ERRORLEVEL 1 (
    pip install -r "%REQ%" && copy /y "%REQ%" "%REQ_ENV%"
)
endlocal
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
set "PATHEXT=.PY;%PATHEXT%"
set "PATH=%~dp0\bin;%PATH%"
