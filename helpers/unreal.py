import sys
import os
import json
import subprocess
import shutil
from sys import platform
from . import env, test_report


def run(command, cwd=None, shell=platform == "win32"):
    return subprocess.check_call(command, cwd=cwd, shell=shell)


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


def create_plugin_dummy_project(plugin, test_path):
    if os.path.isfile(test_path):
        raise AutomationError(f"Test path '{test_path}' is a file.")
    elif not os.path.isdir(test_path):
        os.makedirs(test_path)
    elif os.listdir(test_path):  # not empty?
        raise AutomationError(f"Test path '{test_path}' is not empty.")

    # Create dummy .uproject file
    uproject_file = os.path.join(test_path, f"{plugin.name}.uproject")
    file = open(uproject_file, 'w')
    file.write('{ \
        "FileVersion": 3, \
        "Plugins": \
        [ \
            { \
                "Name": "' + plugin.name + '", \
                "Enabled": true \
            } \
        ] \
    }')
    file.close()

    # Get the plugin directory in the host project, and copy all the files in
    host_plugin_dir = os.path.join(test_path, "Plugins", plugin.name)

    # Copy plugin into host project
    shutil.copytree(plugin.build_path, host_plugin_dir,
                    ignore=shutil.ignore_patterns('Intermediate'))

    return uproject_file


class InvalidUATError(Exception):
    pass


class AutomationError(Exception):
    pass


class UAT(object):
    version = None
    is_default_engine_path = False
    engine_path = None
    uat_file = None

    def __init__(self, version=None, engine_path=None):
        self.version = version
        if engine_path:
            print(f"-- Using custom engine path for version {version}")
            self.engine_path = engine_path
        else:
            self.is_default_engine_path = True
            print(f"-- Finding engine path for version {version}")
            if platform == "linux" or platform == "linux2":
                self.engine_path = get_default_engine_path_linux(version)
            elif platform == "win32":
                self.engine_path = get_default_engine_path_win(version)
        print(f"   {self.engine_path}")

        if not os.path.isdir(self.engine_path):
            raise InvalidUATError(
                f"Engine path '{self.engine_path}' not found.")

        scripts_path = os.path.join(
            self.engine_path, "Engine", "Build", "BatchFiles")
        if platform == "win32":
            self.uat_file = os.path.join(scripts_path, "RunUAT.bat")
        else:
            self.uat_file = os.path.join(scripts_path, "RunUAT.sh")

        if not os.path.isfile(self.uat_file):
            raise InvalidUATError(
                f"UAT not found at '{self.uat_file}'.")

    def run(self, args):  # Run UAT command
        command = [self.uat_file]
        command.extend(args)
        print("   UAT: \"{}\"".format(" ".join(args)))
        return run(command, self.engine_path)

    def build_project(self, project: env.Project, config, all_platforms=False):
        args = ["BuildCookRun",
                f"-project={project.uproject_file}",
                "-build",
                "-compile",
                "-nocompileeditor",
                # f"-target={project.name}Game",
                f"-clientconfig={config}",
                f"-serverconfig={config}",
                "-cook",
                "-stage",
                "-package",
                "-pak",
                "-compressed",
                "-archive",
                f"-archivedirectory={project.build_path}",
                "-prereqs",
                "-zenstore",
                "-utf8output"]
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
        # TODO: For windows: -clientarchitecture = x64  arm64
        if target_platforms:
            print(target_platforms)

            platform_list = '+'.join(target_platforms)
            args.append(f"-targetplatforms={platform_list}")

        try:
            self.run(args)
        except subprocess.CalledProcessError as e:
            print(f"-- Failed")
            sys.exit(e.returncode)
        print("-- Succeeded")

    def build_plugin(self, plugin: env.Plugin, all_platforms=False):
        args = ["BuildPlugin",
                f"-plugin={plugin.uplugin_file}",
                f"-package={plugin.build_path}", "-rocket"]
        if not all_platforms:
            if platform == "linux" or platform == "linux2":
                target_platform = "Linux"
            elif platform == "win32":
                target_platform = "Win64"

            if target_platform:
                args.append(f"-targetplatforms={target_platform}")

        try:
            self.run(args)
        except subprocess.CalledProcessError as e:
            print(f"-- Failed")
            sys.exit(e.returncode)
        print("-- Succeeded")

    def run_automation(self, project, commands, editor=False, config=None, headless=True):
        args = ["RunUnreal",
                "-nop4",
                "-unatended",
                "-nopause",
                "-nosplash",
                f"-project={project.uproject_file}",
                f"-args=-log -abslog={project.get_logs_path()}/{project.name}.log"]
        if headless:
            args.append("-nullrhi")

        if editor:
            args.extend(["-build=editor"])
        else:
            args.extend([
                "-packaged",
                f"-build={project.build_path if project.build_path else 'local'}"])

        if config:
            args.append(f"-configuration={config}")

        args.append(f"-ExecCmds=automation {';'.join(commands)};quit")

        try:
            self.run(args)
        except subprocess.CalledProcessError as e:
            print("-- Failed")
            sys.exit(e.returncode)
        print("-- Succeeded")

    def run_plugin_tests(self, plugin: env.Plugin, test_path, all: bool, filters, tests, headless=True):
        print("\n-- Create test dummy project")
        uproject_file = create_plugin_dummy_project(plugin, test_path)
        project = env.Project(plugin.name, test_path)
        try:
            self.run_project_tests(project, all, filters,
                                   tests, True, None, headless)

            # Copy report back into plugin
            report_path = os.path.join(plugin.path, "Report.xml")
            project_report_path = os.path.join(project.path, "Report.xml")
            if os.path.isfile(report_path):
                os.remove(report_path)
            if os.path.isfile(project_report_path):
                shutil.copy(project_report_path, report_path)
        finally:
            shutil.rmtree(test_path, ignore_errors=True)

    def run_project_tests(self, project: env.Project, all: bool, filters, tests, editor: bool = False, config=None, headless=True):
        commands = []
        if all:
            print("   All Tests")
            commands.append('RunAll')
        if len(filters) > 0:
            print(f"   Filters: {' '.join(filters)}")
            for filter in filters:
                commands.append("RunFilter {filter}")
        # Enqueue a 'RunTests' command for any individual test names that were specified
        if len(tests) > 0:
            print(f"   Tests: {' '.join(tests)}")
            commands.append(f"RunTests Now {'+'.join(tests)}")

        if not commands:  # By default we run Product tests
            print("   No tests or filters to run, defaulting to Product tests.")
            print("   Filters: Product")
            commands.append("RunFilter Product")

        try:
            self.run_automation(project, commands,
                                editor, config, headless)
        finally:
            test_report.generate_project(project)

    def list_plugin_tests(self, plugin: env.Plugin, test_path):
        print("\n-- Create test dummy project")
        uproject_file = create_plugin_dummy_project(plugin, test_path)
        project = env.Project(plugin.name, test_path)
        try:
            self.list_project_tests(project, True, None)
        finally:
            shutil.rmtree(test_path, ignore_errors=True)

    def list_project_tests(self, project: env.Project, editor=False, config=None):
        self.run_automation(project, ["List"],
                            editor, config, True)
