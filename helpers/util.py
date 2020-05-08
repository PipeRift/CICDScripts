import subprocess
import sys

def install(packages):
    command = [sys.executable, "-m", "pip", "install"];
    command.append(packages)
    subprocess.call(command)
