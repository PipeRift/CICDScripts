import sys
import os
import json
import subprocess
import shutil
from platform import system
from . import env, test_report, util
from helpers.util import *
from enum import Enum


# UEBuildTarget.cs:1066
class TargetConfiguration(Enum):
    # Unknown = 0
    Debug = 1
    DebugGame = 2
    Development = 3
    Test = 4
    Shipping = 5

# TargetRules.cs:21
class TargetType(Enum):
    Game = 1
    Editor = 2
    Client = 3
    Server = 4
    Program = 5

class IDE(Enum):
    # Unknown = 0
    VisualStudio = 1
    VSCode = 2

def as_short(full):
    if not full:
        return None
    return '.'.join(full.split('.')[:2])

def as_compact(full):
    if not full:
        return None
    return ''.join(full.split('.')[:2])

def get_default_engine_path_win(version):
    version = as_short(version)
    import winreg

    # Try to find engine in registry
    reg_path = rf"SOFTWARE\EpicGames\Unreal Engine\{version}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as key:
            install_location = winreg.QueryValueEx(key, "InstalledDirectory")[0]
            if os.path.exists(install_location):
                return install_location
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
                        install_location = data.get("InstallLocation")
                        if os.path.exists(install_location):
                            return install_location
            except (json.JSONDecodeError, IOError):
                continue

    # Fallback to hardcoded path
    return os.path.join(os.environ.get(
        'ProgramW6432'), "Epic Games", "UE_{}".format(version))


def get_default_engine_path_linux(version):
    image_engine_path = os.path.join("/home", "ue4", "UnrealEngine")
    if os.path.isdir(image_engine_path):
        return image_engine_path


def find_engine_version(engine_path):
    build_version_file = os.path.join(engine_path, "Engine", "Build", "Build.version")
    if not os.path.isfile(build_version_file):
        return "Custom"
    with open(build_version_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return f"{data['MajorVersion']}.{data['MinorVersion']}.{data.get('PatchVersion', 0)}"


def create_host_project(path, plugins):
    if os.path.isfile(path):
        raise AutomationError(f"Host project path '{path}' is a file.")
    elif not os.path.isdir(path):
        os.makedirs(path)
    elif os.listdir(path):  # not empty?
        raise AutomationError(f"Host project path '{path}' is not empty.")

    # Create dummy .uproject file
    file = open(os.path.join(path, f"HostProject.uproject"), 'w')
    plugin_jsons = map(lambda plugin: f"{{ \"Name\": \"{plugin.name}\", \"Enabled\": true }}", plugins)
    file.write(f"{{ \"FileVersion\": 3, \"Plugins\": [{', '.join(plugin_jsons)}] }}")
    file.close()

    # Copy plugins into host project
    for plugin in plugins:
        shutil.copytree(plugin.path, os.path.join(path, "Plugins", plugin.name),
            ignore=shutil.ignore_patterns('Extras', 'Intermediate', 'Docs', 'Build', 'Vault'))

    return env.Project("HostProject", path)


class InvalidEngineError(Exception):
    pass


class AutomationError(Exception):
    pass

class GenerateProjectConfig(object):
    ide = IDE.VisualStudio
    additional_args = []

class BuildProjectConfig(object):
    target_platforms = [] # Specify a list of target platforms to build. Default is all the Rocket target platforms.
    target_type = TargetType.Game
    configuration = TargetConfiguration.Development
    cook = True
    package = True
    additional_args = []
    settings = False
    editor = False



class BuildPluginConfig(object):
    target_platforms = [] # Specify a list of target platforms to build. Default is all the Rocket target platforms.
    strict_includes = True # Disables precompiled headers and unity build in order to check all source files have self-contained headers.
    versioned = True # Do not embed the current engine version into the descriptor


class Unreal(object):
    version = None
    is_source_engine = False
    engine_path = None
    uat_file = None
    image_build_file = None

    @classmethod
    def from_project(cls, project: env.Project, engine_path=None):
        return Unreal(project.get_ue_version(), engine_path, project.path)
    @classmethod
    def from_plugin(cls, plugin: env.Plugin, engine_path=None):
        return Unreal(plugin.get_ue_version(), engine_path, plugin.path)

    def __init__(self, version=None, engine_path=None, cd = os.getcwd()):
        self.version = version
        if self.engine_path:
            self.is_source_engine = True
            self.engine_path = engine_path
        elif os.path.isdir(self.version):
            self.is_source_engine = True
            self.engine_path = self.version
        else: # Launcher engine
            if system() == "Windows":
                self.engine_path = get_default_engine_path_win(version)
            elif system() == "Linux":
                self.engine_path = get_default_engine_path_linux(version)

        if self.is_source_engine:
            if not os.path.isabs(self.engine_path):
                self.engine_path = os.path.join(cd, self.engine_path)

            self.version = find_engine_version(self.engine_path)
            print(f"-- Using source engine path for version {as_short(self.version)}")
        else:
            print(f"-- Using launcher engine path for version {as_short(self.version)}")
        print(f"   {self.engine_path}")

        if not os.path.isdir(self.engine_path):
            raise InvalidEngineError(
                f"Engine path '{self.engine_path}' not found.")

        if system() == "Windows":
            self.uat_file = os.path.join(self.engine_path, "Engine", "Build", "BatchFiles", "RunUAT.bat")
        else:
            self.uat_file = os.path.join(self.engine_path, "Engine", "Build", "BatchFiles", "RunUAT.sh")
        if not os.path.isfile(self.uat_file):
            raise InvalidEngineError(
                f"UnrealAutomationTool not found at '{self.uat_file}'.")

        self.ubt_file = os.path.join(self.engine_path, "Engine", "Binaries", "DotNET", "UnrealBuildTool", "UnrealBuildTool.exe")
        if not os.path.isfile(self.ubt_file):
            raise InvalidEngineError(
                f"UnrealBuildTool not found at '{self.ubt_file}'.")

        images_path = os.path.join(
            self.engine_path, "Engine", "Extras", "Containers", "Dockerfiles")
        if system() == "Windows":
            self.image_build_file = os.path.join(images_path, "windows", "Build.bat")
        else:
            self.image_build_file = os.path.join(images_path, "linux", "Build.sh")

    def run_UAT(self, args):  # Run UAT command
        command = [self.uat_file]
        command.extend(args)
        print("   UAT: \"{}\"".format(" ".join(args)))
        return run(command, self.engine_path)

    def run_UBT(self, args):  # Run UBT command
        command = [self.ubt_file]
        command.extend(args)
        print("   UBT: \"{}\"".format(" ".join(args)))
        return run(command, self.engine_path)

    def generate_project(self, project: env.Project, config: GenerateProjectConfig):
        result = 0
        platform = get_host_platforms()[0] # For now just use the first
        args = [
            f"-project={project.uproject_file}",
            "-game",
            "-engine",
            "-mode=GenerateProjectFiles",
            f"{project.name}Editor",
            "Development",
            to_ubt_platform(platform)
        ]
        if config.ide and config.ide != IDE.VisualStudio:
            args.append(f"-{config.ide.name}")
        args.extend(config.additional_args)

        try:
            self.run_UBT(args)
        except subprocess.CalledProcessError as e:
            result = -1
        return result

    def generate_clang_db(self, project: env.Project, config: GenerateProjectConfig):
        result = 0
        platform = get_host_platforms()[0] # For now just use the first
        args = [
            f"-project={project.uproject_file}",
            "-game",
            "-engine",
            "-mode=GenerateClangDatabase",
            f"{project.name}Editor",
            "Development",
            to_ubt_platform(platform)
        ]
        match config.ide:
            case IDE.VisualStudio:
                args.append(f"-OutputDir={project.path}/.vs")
            case IDE.VSCode:
                args.append(f"-OutputDir={project.path}/.vscode")
        args.extend(config.additional_args)

        try:
            self.run_UBT(args)
        except subprocess.CalledProcessError as e:
            result = -1
        return result

    def build_project(self, project: env.Project, config: BuildProjectConfig):
        result = 0
        for platform in config.target_platforms:
            print(f"-- Building platform {colors.OKGREEN}{platform}{colors.ENDC}")
            args = ["BuildCookRun",
                f"-project={project.uproject_file}",
                "-build",
                "-compile",
                # f"-target={project.name}Game",
                f"-clientconfig={config.configuration.name}",
                f"-serverconfig={config.configuration.name}",
                "-utf8output"
            ]

            ubt_platform = util.to_ubt_platform(platform)
            if ubt_platform:
                args.append(f"-platform={ubt_platform}")
            ubt_arch = util.to_ubt_architecture(platform)
            if ubt_arch:
                args.append(f"-specifiedarchitecture={ubt_arch}")

            if config.cook:
                args.extend(["-cook", "-zenstore"])

            if config.package:
                args.extend([
                    # Stage
                    "-stage",
                    "-prereqs",
                    # Package
                    "-package",
                    "-pak",
                    "-compressed",
                    "-archive",
                    f"-archivedirectory={project.build_path}"
                ])

            if not config.editor:
                args.append("-nocompileeditor")

            args.extend(config.additional_args)

            try:
                self.run_UAT(args)
            except subprocess.CalledProcessError as e:
                result = -1
        return result

    def build_plugin(self, plugin: env.Plugin, config: BuildPluginConfig, plugin_dependencies = []):
        args = ["BuildPlugin",
            f"-plugin={plugin.uplugin_file}",
            f"-package={plugin.build_path}", "-rocket",
            "-Architecture_Windows=arm64+x64",
            # "-Architecture_Linux=arm64+x64", Linux is considered two different platforms: Linux and LinuxARM64 (why epic?)
            "-Architecture_Mac=arm64+x64",
            "-Architecture_Android=arm64+x64",
            "-Architecture_IOS=arm64",
            "-StrictIncludes"
        ]

        if config.target_platforms:
            args.append(f"-targetplatforms={'+'.join(map(to_ubt_platform, config.target_platforms))}")

        try:
            self.run_UAT(args)
        except subprocess.CalledProcessError as e:
            return -1

        # Try to find and import build.py of the plugin
        result = 0
        plugin_build = util.import_from_path(plugin.name, os.path.join(plugin.path, "build.py"))
        if plugin_build:
            if plugin_build.get_additional_plugins:
                plugin_paths = plugin_build.get_additional_plugins()
                addt_plugins = []
                for path in plugin_paths:
                    try:
                        addt_plugin = env.Plugin(None, os.path.join(plugin.path, path))
                        addt_plugin.build_path = os.path.join(plugin.build_path, path)
                        addt_plugins.append(addt_plugin)
                    except: # Not a plugin
                        print(f"Not a plugin '{path}'")

                # Build additional plugins into relative build folder
                if addt_plugins:
                    print(f"{colors.OKGREEN}-- Building additional plugins: {colors.OKGREEN}{' '.join(map(lambda plugin: plugin.name, addt_plugins))}{colors.ENDC}")
                    engine_plugins_path = os.path.join(self.engine_path, "Engine", "Plugins")
                    plugin_was_installed = False
                    if os.path.isdir(os.path.join(engine_plugins_path, plugin.name)) or os.path.isdir(os.path.join(engine_plugins_path, "Marketplace", plugin.name)):
                        plugin_was_installed = True

                    if not plugin_was_installed:
                        print(f"Installing base plugin in engine temporarily")
                        shutil.copytree(plugin.build_path, os.path.join(engine_plugins_path, "Marketplace", plugin.name))

                    for addt_plugin in addt_plugins:
                        r = self.build_plugin(addt_plugin, config, [plugin])
                        if result == 0:
                            result = r
                    
                    if not plugin_was_installed:
                        shutil.rmtree(os.path.join(engine_plugins_path, "Marketplace", plugin.name), ignore_errors=True)

            if plugin_build.get_copy_post_build:
                post_build_paths = plugin_build.get_copy_post_build()
                print(f"{colors.OKGREEN}-- Copying post-build files{colors.ENDC}")
                for path in post_build_paths:
                    src = os.path.join(plugin.path, path)
                    dst = os.path.join(plugin.build_path, path)
                    print(f"'{src}' to '{dst}'")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    elif os.path.isfile(src):
                        shutil.copy2(src, dst)

        return result
    
    def package_plugin(self, plugin: env.Plugin, package_path):
        ignore = shutil.ignore_patterns('Extras', 'Intermediate', 'Docs', 'Build', 'Vault')
        shutil.copytree(plugin.path, package_path, ignore = ignore)


    def run_automation(self, project, commands, editor=False, config=None, headless=True):
        args = ["RunUnreal",
                "-nop4",
                "-unattended",
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
            self.run_UAT(args)
        except subprocess.CalledProcessError as e:
            print("-- Failed")
            sys.exit(e.returncode)
        print("-- Succeeded")

    def run_plugin_tests(self, plugin: env.Plugin, test_path, all: bool, filters, tests, headless=True):
        print("\n-- Create test host project")
        host_project = create_host_project(test_path, [plugin])
        try:
            self.run_project_tests(host_project, all, filters,
                                   tests, True, None, headless)

            # Copy report back into plugin
            report_path = os.path.join(plugin.path, "Report.xml")
            project_report_path = os.path.join(host_project.path, "Report.xml")
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
                commands.append(f"RunFilter {filter}")
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
        print("\n-- Create test host project")
        host_project = create_host_project(test_path, [plugin])
        try:
            self.list_project_tests(host_project, True, None)
        finally:
            shutil.rmtree(test_path, ignore_errors=True)

    def list_project_tests(self, project: env.Project, editor=False, config=None):
        self.run_automation(project, ["List"],
                            editor, config, True)

    def build_image(self):
        try:
            command = [self.image_build_file]
            print("   Build Image")
            return run(command, os.path.dirname(self.image_build_file))
        except subprocess.CalledProcessError as e:
            print("-- Failed")
            sys.exit(e.returncode)
        print("-- Succeeded")
