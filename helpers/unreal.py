import os
import subprocess
from .util import install
from sys import platform



def run_uat(args):
    global overrided_engine_path
    global engine_path
    uat_path = os.path.join(engine_path, "Engine", "Build", "BatchFiles")
    uat = os.path.join(uat_path, "RunUAT.sh")
    if platform == "win32":
        uat = os.path.join(uat_path, "RunUAT.bat")
    command = [uat]
    command.extend(args)
    print("-- UAT: \"{}\"".format(" ".join(command)))
    return subprocess.call(command, shell=True)

def set_default_engine_path(version):
    global overrided_engine_path
    global engine_path
    print("-- Finding default engine path for version {}".format(version))
    engine_path = os.path.join(os.environ.get('ProgramW6432'), "Epic Games", "UE_{}".format(version))
    overrided_engine_path = False
    return engine_path != None

def override_engine_path(version, override_path=None):
    global overrided_engine_path
    global engine_path
    overrided_engine_path = False

    if override_path:
        print("-- Using custom engine path for version {}".format(version))
        engine_path = override_path
        overrided_engine_path = True
        return engine_path != None
    else:
        return set_default_engine_path(version)

def clean_engine_path():
    global overrided_engine_path
    global engine_path
    overrided_engine_path = False
    engine_path = None

def build_plugin(plugin, all_platforms=False):
    try:
        if not all_platforms:
            if platform == "linux" or platform == "linux2":
                target_platform = "Linux"
            if platform == "win32":
                target_platform = "Win64"

        args = ['BuildPlugin',
            '-Plugin={}'.format(plugin.upluginFile),
            '-Package={}'.format(plugin.build_path)]
        if target_platform:
            args.append(f"-TargetPlatforms={target_platform}")
        result = run_uat(args)
    except Exception as e:
        print("There was an error!\n{}".format(e or "."))
        return 1
    return result

def test_plugin(plugin):
    last_cwd = os.getcwd()
    os.chdir(plugin.test_path)

    print("-- Run tests")
    # We cant use the manager directly because it manually exits
    result = subprocess.call(["ue4", "test", plugin.name], shell=True)

    print("-- Succeeded" if result == 0 else "-- Failed")
    os.chdir(last_cwd)
    return result
