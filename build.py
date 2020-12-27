import sys

from helpers.util import *
from helpers import ue4, env

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
def plugin(plugin_name, path, build_path, engine_path):
    plugin = env.Plugin(plugin_name, path)
    if build_path:
        plugin.build_path = build_path

    ue4.set_engine_root(plugin.get_short_engine_version(), engine_path)

    click.echo("-- Building {} Plugin".format(plugin.name))
    result = ue4.build_plugin(plugin)

    ue4.clear_engine_root()
    return result

build.add_command(plugin)

if __name__ == '__main__':
    sys.exit(build_plugin())