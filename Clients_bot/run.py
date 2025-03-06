import sys
import subprocess
import time

# Определяем путь к текущему интерпретатору Python
VENV_PYTHON = sys.executable

server_process = subprocess.Popen([VENV_PYTHON, "server/api.py"])
time.sleep(3)
bot_process = subprocess.Popen([VENV_PYTHON, "bot.py"])

server_process.wait()
bot_process.wait()
