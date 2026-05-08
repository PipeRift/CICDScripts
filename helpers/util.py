import shutil
import subprocess
import sys
import os
import shutil
import importlib.util


def install(package):
    if package in sys.modules:
        return
    elif importlib.util.find_spec(package) is not None:
        return
    print("Installing {}".format(package))
    command = [sys.executable, "-m", "pip", "install"]
    command.append(package)
    subprocess.call(command)

def import_from_path(name, path):
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except:
        return None

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


global platforms
# Disabled for now: Windows_arm64
platforms = ["Windows_x64", "Linux_x64",
             "Linux_arm64", "Mac", "Android", "IOS"]


def get_platforms(match):
    return [p for p in platforms if match in p]


def to_ubt_platform(platform):
    os = platform.split('_')[0]
    arch = platform.split('_')[1]
    if os == "Windows":
        return "Win64"
    elif os == "Linux":
        return "Linux" if arch == "x64" else "LinuxArm64"
    return os  # Mac, Android and IOS


def to_ubt_architecture(platform):
    os = platform.split('_')[0]
    arch = platform.split('_')[1]

    if os == "Windows":
        return arch
    return None  # only windows uses architecture in ubt


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
