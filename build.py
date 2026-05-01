from helpers.util import *
from helpers import env, unreal, util
from platform import system
install('click')
import click  # NOQA


@click.group()
def build():
    pass


@click.command()
@click.option('-n', '--name', envvar="CI_PROJECT_NAME", required=True, help="Name of the project (without .uproject)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", type=click.Path(exists=True), help="{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-b', '--build-path', envvar="CI_PROJECT_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-c', '--config', envvar="CI_PROJECT_CONFIG", type=click.Choice(["Debug", "DebugGame", "Development", "Test", "Shipping"], case_sensitive=False), help=f"{colors.OKCYAN}(default: Development){colors.ENDC} Configuration to build in.")
@click.option('-pl', '--platform', envvar="CI_PROJECT_CONFIG", type=click.Choice(util.platforms, case_sensitive=False), multiple=True, help=f"{colors.OKCYAN}(default: Current){colors.ENDC}")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def project(name, path, build_path, engine_path, config, platform, all_platforms):
    """Packages a project for the desired platform. """
    if not config:
        config = "Development"

    project = env.Project(name, path, build_path)
    uat = unreal.UAT(project.get_short_engine_version(), engine_path)

    if not platform:
        if not all_platforms:
            if system() == "Linux":
                platform = util.get_platforms("Linux")
            elif system() == "Windows":
                platform = util.get_platforms("Windows")
            elif system() == "Darwin":
                platform = util.get_platforms("Mac")
        else:
            if system() == "Linux":
                platform = util.get_platforms("Linux")
            elif system() == "Windows":  # Windows can cross-compile to linux
                platform = util.get_platforms(
                    "Windows") + util.get_platforms("Linux")
            elif system() == "Darwin":
                platform = util.get_platforms("Mac")

    platformstext = f'{colors.WARNING}|{colors.OKGREEN}'.join(platform)
    click.echo(
        f"{colors.WARNING}-- Building project {colors.OKGREEN}{project.name}{colors.WARNING} ({colors.OKGREEN}{config}{colors.WARNING}) for {colors.OKGREEN}{platformstext}{colors.ENDC}")

    for pl in platform:
        click.echo(
            f"-- Building platform {colors.OKGREEN}{pl}{colors.ENDC}")
        uat.build_project(project, config, pl)


build.add_command(project)


@click.command()
@click.option('-n', '--name', envvar="CI_PLUGIN_NAME", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PLUGIN_DIR", type=click.Path(exists=True), help="{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all plugin files")
@click.option('-b', '--build-path', envvar="CI_PLUGIN_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def plugin(name, path, build_path, engine_path, all_platforms):
    """Packages a plugin for the desired platform. """
    plugin = env.Plugin(name, path, build_path)
    uat = unreal.UAT(plugin.get_short_engine_version(), engine_path)
    platformstext = 'for all platforms' if all_platforms else "for current platform"
    click.echo(
        f"{colors.WARNING}-- Building plugin {colors.OKGREEN}{plugin.name}{colors.WARNING} {platformstext}{colors.ENDC}")
    uat.build_plugin(plugin, all_platforms)


build.add_command(plugin)

if __name__ == '__main__':
    build()
