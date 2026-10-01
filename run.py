"""
Root-level entry point convenience script.
Allows running: python run.py  (instead of uvicorn app.main:app --reload)

If packages are missing, this script will automatically use the venv Python.
"""
import sys
import os

# Auto-switch to the venv interpreter if not already inside it
VENV_PYTHON = os.path.join(os.path.dirname(__file__), "fitbuddy-env", "Scripts", "python.exe")
if os.path.exists(VENV_PYTHON) and sys.executable != os.path.abspath(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
