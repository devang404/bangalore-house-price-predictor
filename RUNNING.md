Quick run instructions (Windows)

1) Ensure venv exists and dependencies are installed

   # create venv (if missing)
   python -m venv .venv

   # install dependencies into venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt

2) Start the app (choose one)

   # PowerShell (foreground)
   .\.venv\Scripts\python.exe .\app.py

   # PowerShell (convenience script)
   .\start.ps1

   # cmd.exe
   start.bat

Notes
- These scripts explicitly use .venv\Scripts\python.exe so you won't accidentally use a global python that lacks required packages.
- If you prefer activating the venv manually in PowerShell, run:

   . .\.venv\Scripts\Activate.ps1
   python .\app.py

- If you continue to see ModuleNotFoundError for `flask_sqlalchemy` or similar, run:

   .\.venv\Scripts\python.exe -m pip install Flask-SQLAlchemy

and then restart the server using the start script above.
