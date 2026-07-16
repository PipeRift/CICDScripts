from helpers.util import *
from helpers import env, unreal, util, click
from platform import system


@click.group()
def build():
    pass


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", required=True, help="Name of the project (without .uproject)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-b', '--build-path', envvar="CI_BUILD_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-c', '--config', envvar="CI_CONFIG", type=click.Choice(unreal.TargetConfiguration, case_sensitive=False), help=f"{colors.OKCYAN}(default: Development){colors.ENDC} Configuration to build in.")
@click.option('-pl', '--platform', envvar="CI_PLATFORM", type=click.Choice(util.platforms, case_sensitive=False), multiple=True, help=f"{colors.OKCYAN}(default: Current){colors.ENDC}")
@click.option('-a', '--all-platforms', envvar="CI_ALL_PLATFORMS", is_flag=True, help="Build for all platforms available")
@click.option('-ed', '--editor', envvar="CI_BUILD_EDITOR", is_flag=True, help="Build editor binaries")
def project(name, path, build_path, engine_path, config: unreal.TargetConfiguration, platform, all_platforms, editor):
    """Packages a project for the desired platform. """
    if not config:
        config = unreal.TargetConfiguration.Development

    project = env.Project(name, path, build_path)
    ue = unreal.Unreal.from_project(project, engine_path)

    if not platform:
        platform = get_host_platforms()
        if all_platforms:
            if system() == "Windows":  # Windows can cross-compile to linux
                platform.extend(util.get_platforms("Linux"))

    platformstext = f'{colors.WARNING}|{colors.OKGREEN}'.join(platform)
    click.echo(
        f"{colors.WARNING}-- Building project {colors.OKGREEN}{project.name}{colors.WARNING} ({colors.OKGREEN}{config}{colors.WARNING}) for {colors.OKGREEN}{platformstext}{colors.ENDC}")

    settings = unreal.BuildProjectConfig()
    settings.configuration = config
    settings.target_platforms = platform
    settings.editor = editor
    if ue.build_project(project, settings) != 0:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")

build.add_command(project)


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all plugin files")
@click.option('-b', '--build-path', envvar="CI_BUILD_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-pl', '--platform', envvar="CI_PLATFORM", type=click.Choice(util.platforms, case_sensitive=False), multiple=True, help=f"{colors.OKCYAN}(default: Current){colors.ENDC}")
def plugin(name, path, build_path, engine_path, platform):
    """Packages a plugin for the desired platform. """
    plugin = env.Plugin(name, path, build_path)
    ue = unreal.Unreal.from_plugin(plugin, engine_path)
    platformstext = f"for {', '.join(platform)} platforms" if platform else "for default platforms"
    click.echo(
        f"{colors.WARNING}-- Building plugin {colors.OKGREEN}{plugin.name}{colors.WARNING} {platformstext}{colors.ENDC}")

    config = unreal.BuildPluginConfig()
    config.target_platforms = platform
    if ue.build_plugin(plugin, config) != 0:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")



build.add_command(plugin)


@click.command()
@click.option('-t', '--target', 'targets', envvar="CI_TARGETS", multiple=True, required=True, help="Engine target name to build (e.g. ShaderCompileWorker). Can be repeated.")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-c', '--config', envvar="CI_CONFIG", type=click.Choice(unreal.TargetConfiguration, case_sensitive=False), help=f"{colors.OKCYAN}(default: Development){colors.ENDC}")
@click.option('-pl', '--platform', envvar="CI_PLATFORM", type=click.Choice(util.platforms, case_sensitive=False), multiple=True, help=f"{colors.OKCYAN}(default: Current){colors.ENDC}")
def engine(targets, engine_path, config, platform):
    """Builds engine targets (e.g. ShaderCompileWorker) using UnrealBuildTool. """
    if not config:
        config = unreal.TargetConfiguration.Development
    if not platform:
        platform = get_host_platforms()

    ue = unreal.Unreal.from_engine_path(engine_path)

    settings = unreal.BuildEngineConfig()
    settings.configuration = config
    settings.target_platforms = platform

    platformstext = f'{colors.WARNING}|{colors.OKGREEN}'.join(platform)
    click.echo(
        f"{colors.WARNING}-- Building engine targets {colors.OKGREEN}{", ".join(targets)}{colors.WARNING} ({colors.OKGREEN}{config.name}{colors.WARNING}) for {colors.OKGREEN}{platformstext}{colors.ENDC}")

    if ue.build_engine(list(targets), settings) != 0:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")

build.add_command(engine)


@click.command()
@click.option('-v', '--engine-version', envvar="CI_ENGINE_VERSION", help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
def image(engine_version, engine_path):
    """Builds an Unreal Engine container image """
    ue = unreal.Unreal(engine_version, engine_path)
    click.echo(
        f"{colors.WARNING}-- Building image for {colors.OKGREEN}{engine_version}{colors.ENDC}")
    ue.build_image()

build.add_command(image)


if __name__ == '__main__':
    build()
