import shutil
import subprocess
import sys
import os
import shutil


def install(packages):
    print("Installing {}".format(packages))
    command = [sys.executable, "-m", "pip", "install"];
    command.append(packages)
    subprocess.call(command)

def create_or_empty(path):
    if os.path.exists(path):
        shutil.rmtree(path, True)
    if not os.path.exists(path):
        os.makedirs(path)

def remove(path):
    if os.path.isdir(path):
        shutil.rmtree(path, True)
        return True
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'