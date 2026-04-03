import sys
import os
import json
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
    print("   UAT: \"{}\"".format(" ".join(args)))
    return run(command, get_engine_path(), shell=platform == "win32")


def get_default_engine_path_win(version):
    import winreg

    # Try to find engine in registry
    reg_path = rf"SOFTWARE\EpicGames\Unreal Engine\{version}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, "InstalledDirectory")[0]
    except (FileNotFoundError, OSError):
        pass

    # Try to find engine from launcher manifests
    manifest_path = os.path.join(os.environ.get(
        "ProgramData", "C:/ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests")
    print(manifest_path)
    if os.path.isdir(manifest_path):
        from pathlib import Path
        for manifest_file in Path(manifest_path).glob("*.item"):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Look for "UE_5.7" or similar
                    if version in data.get("MandatoryAppFolderName", ""):
                        return data.get("InstallLocation")
            except (json.JSONDecodeError, IOError):
                continue

    # Fallback to hardcoded path
    return os.path.join(os.environ.get(
        'ProgramW6432'), "Epic Games", "UE_{}".format(version))


def get_default_engine_path_linux(version):
    image_engine_path = os.path.join("home", "ue4", "UnrealEngine")
    if os.path.isdir(image_engine_path):
        return image_engine_path


def set_default_engine_path(version):
    global overrided_engine_path
    global engine_path

    print(f"-- Finding engine path for version {version}")
    if platform == "linux" or platform == "linux2":
        engine_path = get_default_engine_path_linux(version)
    elif platform == "win32":
        engine_path = get_default_engine_path_win(version)
    overrided_engine_path = False
    print(f"   {engine_path}")
    return engine_path != None


def override_engine_path(version, override_path=None):
    global overrided_engine_path
    global engine_path
    overrided_engine_path = False
    if override_path:
        print(f"-- Using custom engine path for version {version}")
        engine_path = override_path
        overrided_engine_path = True
        print(f"   {engine_path}")
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
            f"-archivedirectory={project.build_path}",
            f"-clientconfig={config}",
            "-cook",
            "-build",
            "-stage",
            "-pak",
            "-archive"]
    target_platforms = []
    if not all_platforms:
        if platform == "linux" or platform == "linux2":
            target_platforms.extend(["Linux", "LinuxArm64"])
        elif platform == "win32":
            target_platforms.extend(["Win64", "WinArm64"])
    else:
        if platform == "linux" or platform == "linux2":
            target_platforms.extend(["Linux", "LinuxArm64"])
        elif platform == "win32":  # Windows can cross-compile to linux
            target_platforms.extend(
                ["Win64", "WinArm64", "Linux", "LinuxArm64"])

    if target_platforms:
        print(target_platforms)

        platform_list = '+'.join(target_platforms)
        args.append(f"-targetplatforms={platform_list}")

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
