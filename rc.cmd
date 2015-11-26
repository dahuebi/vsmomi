set VENV=ENV
python -m virtualenv %VENV%

call %VENV%\Scripts\activate.bat
pip install -r requirements.txt
set PYTHONPATH=%CD%
set PATHEXT=.PY;%PATHEXT%
set PATH=%CD%\bin;%PATH%
