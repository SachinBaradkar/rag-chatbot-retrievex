#!/usr/bin/env python3
"""
Entry point — run with:  python run.py
Or directly:             streamlit run app/ui/streamlit_app.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    app_path = Path(__file__).parent / "app" / "ui" / "streamlit_app.py"
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
