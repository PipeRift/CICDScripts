from helpers.util import *
from helpers import env, unreal

install('click')
import click

@click.group()
def build():
    pass

@click.command()
@click.option('-n', '--project-name', envvar="CI_PROJECT_NAME", required=True, help="Name of the project (without .uproject)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", required=True, type=click.Path(exists=True), help="Path that contains all project files")
@click.option('-b', '--build-path', envvar="CI_PROJECT_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-c', '--config', envvar="CI_PROJECT_CONFIG", help=f"{colors.OKCYAN}(default: Shipping){colors.ENDC} Valid: 'Debug', 'DebugGame', 'Development', 'Test' and 'Shipping'.")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def project(project_name, path, build_path, engine_path, config, all_platforms):
    """Packages a project for the desired platform. """
    if not config:
        config = "Shipping"

    project = env.Project(project_name, path, build_path)
    unreal.override_engine_path(project.get_short_engine_version(), engine_path)
    click.echo(f"{colors.WARNING}-- Building {project.name} Project{colors.ENDC} for {config}")
    unreal.build_project(project, config, all_platforms)
build.add_command(project)

@click.command()
@click.option('-n', '--plugin-name', envvar="CI_PLUGIN_NAME", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PLUGIN_DIR", required=True, type=click.Path(exists=True), help="Path that contains all plugin files")
@click.option('-b', '--build-path', envvar="CI_PLUGIN_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def plugin(plugin_name, path, build_path, engine_path, all_platforms):
    """Packages a plugin for the desired platform. """
    plugin = env.Plugin(plugin_name, path, build_path)
    unreal.override_engine_path(plugin.get_short_engine_version(), engine_path)
    click.echo(f"{colors.WARNING}-- Building {plugin.name} Plugin{colors.ENDC}")
    unreal.build_plugin(plugin, all_platforms)
build.add_command(plugin)

if __name__ == '__main__':
    build()