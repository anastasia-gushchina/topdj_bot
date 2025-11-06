#!/bin/bash
set -e  # Exit on first fail

export PYTHONUNBUFFERED=0

source /app/venv/bin/activate


case "$1" in
    web)
        echo starting server...
        alembic upgrade head
        exec uvicorn main:app --host 0.0.0.0 --port 8000 --loop=asyncio --workers=1
    ;;
    web_dev)
        echo starting server...
        alembic upgrade head
        exec uvicorn main:app --host 0.0.0.0 --port 8000 --loop=asyncio --reload
    ;;
    test)
        pytest -s -v src/tests
    ;;
    *)
        $@
    ;;
esac
