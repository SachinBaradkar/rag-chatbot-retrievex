"""
Hugging Face Spaces entry point.
HF Spaces expects a file named app.py in the root.
This simply delegates to the Streamlit app.
"""
# HF Spaces auto-detects streamlit when requirements.txt includes it
# and looks for app.py. We just import so the module tree is loaded.
from app.ui.streamlit_app import *  # noqa: F401, F403
