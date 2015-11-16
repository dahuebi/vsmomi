python -m virtualenv .

source bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
export PATH=$PWD/bin:$PATH
