import os
import shutil

print("FFmpeg in PATH?", shutil.which("ffmpeg"))
print("System PATH:", os.environ["PATH"])
