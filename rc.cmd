set VENV=ENV
python -m virtualenv "%VENV%"

call "%VENV%\Scripts\activate.bat"
pip install -r "%~dp0\requirements.txt"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
set "PATHEXT=.PY;%PATHEXT%"
set "PATH=%~dp0\bin;%PATH%"
