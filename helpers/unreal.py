import sys
import os
import subprocess
from .util import install
from sys import platform


def run(command, cwd=None, shell=False):
    return subprocess.check_call(command, cwd=cwd, shell=shell)

def run_uat(args):
    global overrided_engine_path
    global engine_path
    uat_path = os.path.join("Engine", "Build", "BatchFiles")
    uat = os.path.join(uat_path, "RunUAT.sh")
    if platform == "win32":
        uat = os.path.join(uat_path, "RunUAT.bat")
    command = [uat]
    command.extend(args)
    print("-- UAT: \"{}\"".format(" ".join(command)))
    return run(command, get_engine_path(), shell=platform == "win32")

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

def get_engine_path():
    return engine_path

def build_project(project, config="Shipping", all_platforms=False):
    args = ["BuildCookRun",
        f"-project={project.uprojectFile}",
        f"-package={project.build_path}",
        f"-clientconfig={config}"]
    if not all_platforms:
        if platform == "linux" or platform == "linux2":
            target_platform = "Linux"
        elif platform == "win32":
            target_platform = "Win64"

        if target_platform:
            args.append(f"-targetplatforms={target_platform}")

    try:
        run_uat(args)
    except subprocess.CalledProcessError as e:
        print(f"-- Failed")
        sys.exit(e.returncode)
    print("-- Succeeded")

def build_plugin(plugin, all_platforms=False):
    args = ["BuildPlugin",
        f"-plugin={plugin.upluginFile}",
        f"-package={plugin.build_path}", "-rocket"]
    if not all_platforms:
        if platform == "linux" or platform == "linux2":
            target_platform = "Linux"
        elif platform == "win32":
            target_platform = "Win64"

        if target_platform:
            args.append(f"-targetplatforms={target_platform}")

    try:
        run_uat(args)
    except subprocess.CalledProcessError as e:
        print(f"-- Failed")
        sys.exit(e.returncode)
    print("-- Succeeded")

def test_plugin(plugin):
    last_cwd = os.getcwd()
    os.chdir(plugin.test_path)

    print("-- Run tests")
    # We cant use the manager directly because it manually exits
    result = subprocess.call(["ue4", "test", plugin.name], shell=True)

    print("-- Succeeded" if result == 0 else "-- Failed")
    os.chdir(last_cwd)
    return result
