python -m virtualenv .

call Scripts/activate.bat
pip install -r requirements.txt
set PYTHONPATH=%CD%
set PATHEXT=.PY;%PATHEXT%
