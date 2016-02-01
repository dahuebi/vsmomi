SAVED_OPTIONS=$(set +o)
trap "eval \"$SAVED_OPTIONS\"" INT TERM QUIT

WD="`dirname "${BASH_SOURCE[0]}"`"
cd "$WD"
WD="`pwd`"
cd - > /dev/null

VENV=env
DONE=env/.done
if ! [ -e "$DONE" ]; then
    python2 -m virtualenv "$VENV" && \
        touch "$DONE"
fi

source "$VENV/bin/activate"
REQ="$WD/requirements.txt"
REQ_ENV="$VENV/requirements.txt"
if ! diff "$REQ" "$REQ_ENV" > /dev/null; then
    pip install -r "$WD/requirements.txt" && \
        cp -f "$REQ" "$REQ_ENV"
fi
export PYTHONPATH="$WD:$PYTHONPATH"
export PATH="$WD/bin:$PATH"
