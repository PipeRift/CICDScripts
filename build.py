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
@click.option('-c', '--config', envvar="CI_CONFIG", type=click.Enum(unreal.TargetConfiguration, case_sensitive=False), help=f"{colors.OKCYAN}(default: Development){colors.ENDC} Configuration to build in.")
@click.option('-pl', '--platform', envvar="CI_PLATFORM", type=click.Choice(util.platforms, case_sensitive=False), multiple=True, help=f"{colors.OKCYAN}(default: Current){colors.ENDC}")
@click.option('-a', '--all-platforms', envvar="CI_ALL_PLATFORMS", is_flag=True, help="Build for all platforms available")
def project(name, path, build_path, engine_path, config, platform, all_platforms):
    """Packages a project for the desired platform. """
    if not config:
        config = "Development"

    project = env.Project(name, path, build_path)
    uat = unreal.UAT(project.get_short_engine_version(), engine_path)

    if not platform:
        platform = get_host_platforms()
        if all_platforms:
            if system() == "Windows":  # Windows can cross-compile to linux
                platform.append(util.get_platforms("Linux"))

    platformstext = f'{colors.WARNING}|{colors.OKGREEN}'.join(platform)
    click.echo(
        f"{colors.WARNING}-- Building project {colors.OKGREEN}{project.name}{colors.WARNING} ({colors.OKGREEN}{config}{colors.WARNING}) for {colors.OKGREEN}{platformstext}{colors.ENDC}")

    settings = unreal.BuildProjectConfig()
    settings.config = config
    settings.target_platforms = platform
    if uat.build_project(project, settings) != 0:
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
    uat = unreal.UAT(plugin.get_short_engine_version(), engine_path)
    platformstext = f'for {', '.join(platform)} platforms' if platform else "for default platforms"
    click.echo(
        f"{colors.WARNING}-- Building plugin {colors.OKGREEN}{plugin.name}{colors.WARNING} {platformstext}{colors.ENDC}")
    
    config = unreal.BuildPluginConfig()
    config.target_platforms = platform
    if uat.build_plugin(plugin, config) != 0:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")



build.add_command(plugin)


@click.command()
@click.option('-v', '--engine-version', envvar="CI_ENGINE_VERSION", required=True, help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
def image(engine_version, engine_path):
    """Builds an Unreal Engine container image """
    uat = unreal.UAT(engine_version, engine_path)
    click.echo(
        f"{colors.WARNING}-- Building image for {colors.OKGREEN}{engine_version}{colors.ENDC}")
    uat.build_image()

build.add_command(image)


if __name__ == '__main__':
    build()
