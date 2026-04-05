import click
from helpers.util import *
from helpers import env, unreal

install('click')


@click.group()
def build():
    pass


@click.command()
@click.option('-n', '--name', envvar="CI_PROJECT_NAME", required=True, help="Name of the project (without .uproject)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", type=click.Path(exists=True), help="{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-b', '--build-path', envvar="CI_PROJECT_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-c', '--config', envvar="CI_PROJECT_CONFIG", help=f"{colors.OKCYAN}(default: Development){colors.ENDC} Valid: 'Debug', 'DebugGame', 'Development', 'Test' and 'Shipping'.")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def project(name, path, build_path, engine_path, config, all_platforms):
    """Packages a project for the desired platform. """
    if not config:
        config = "Development"

    project = env.Project(name, path, build_path)
    uat = unreal.UAT(project.get_short_engine_version(), engine_path)
    click.echo(
        f"-- Building project {colors.OKGREEN}{project.name}{colors.ENDC} for {colors.OKGREEN}{config}{colors.ENDC}")
    uat.build_project(project, config, all_platforms)


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
    click.echo(
        f"{colors.WARNING}-- Building {plugin.name} Plugin{colors.ENDC}")
    uat.build_plugin(plugin, all_platforms)


build.add_command(plugin)

if __name__ == '__main__':
    build()
