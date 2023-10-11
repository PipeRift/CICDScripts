from helpers.util import *
from helpers import env, unreal

install('click')
import click

@click.group()
def build():
    pass

@click.command()
@click.option('-n', '--plugin-name', envvar="CI_PLUGIN", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", required=True, type=click.Path(exists=True), help="Path that contains all plugin files")
@click.option('-b', '--build-path', envvar="CI_PLUGIN_BUILD_DIR", type=click.Path(exists=True), help="Destination of the packaged plugin (default: {path}/Build)")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help="Path to the engine (default: auto-discovered)")
@click.option('-a', '--all-platforms', is_flag=True, help="Build for all platforms available")
def plugin(plugin_name, path, build_path, engine_path, all_platforms):
    plugin = env.Plugin(plugin_name, path, build_path)
    unreal.override_engine_path(plugin.get_short_engine_version(), engine_path)
    click.echo(f"{colors.WARNING}-- Building {plugin.name} Plugin{colors.ENDC}")
    unreal.build_plugin(plugin, all_platforms)

build.add_command(plugin)

if __name__ == '__main__':
    build()