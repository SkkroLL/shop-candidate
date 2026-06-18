@echo off
echo Creating a virtual environment...
python -m venv .venv
echo Installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt
echo Installation is complete!
pause