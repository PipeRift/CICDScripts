import os
import subprocess
from .util import install

def prepare(env):
    print("\n-- Install ue4cli")
    install('ue4cli')

    print("-- Setup ue4cli")
    subprocess.call(["ue4", "setroot", env.engine_path], shell=True)

def test(env):
    prevCD = os.getcwd()
    os.chdir(env.test_path)

    print("-- Run tests")
    result = subprocess.call(["ue4", "test", env.plugin], shell=True)
    if result != 0:
        print("-- Failed")
        os.chdir(prevCD)
        return -1

    print("-- Succeeded")
    os.chdir(prevCD)
    return 0