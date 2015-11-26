VENV=env
python -m virtualenv $VENV

source $VENV/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
export PATH=$PWD/bin:$PATH
