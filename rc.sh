WD="`dirname "${BASH_SOURCE[0]}"`"
cd "$WD"
WD="`pwd`"
cd - > /dev/null

VENV=env
python2 -m virtualenv "$VENV"

source "$VENV/bin/activate"
pip install -r "$WD/requirements.txt"
export PYTHONPATH="$WD:$PYTHONPATH"
export PATH="$WD/bin:$PATH"
