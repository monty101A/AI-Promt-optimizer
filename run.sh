#!/usr/bin/env bash
# One-click start for Mac/Linux: creates venv, installs packages, makes .env, runs the app.
cd "$(dirname "$0")" || exit 1

if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || { echo "Python 3 not found."; exit 1; }
fi

source venv/bin/activate
echo "Installing requirements..."
pip install -q -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Open it, paste your GEMINI_API_KEY, then run ./run.sh again."
    exit 0
fi

streamlit run app.py
