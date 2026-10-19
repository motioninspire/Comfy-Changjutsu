"""Run by ComfyUI-Manager after cloning. Installs pip requirements only."""
import subprocess, sys
from pathlib import Path
req = Path(__file__).parent / "requirements.txt"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
