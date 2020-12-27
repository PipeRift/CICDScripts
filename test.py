import sys
import os
import shutil

from helpers.util import *
from helpers import env, ue4, test_report

install('click')
import click


@click.group()
def test():
    pass

@click.command()
@click.option('-n', '--plugin-name', envvar="CI_PLUGIN", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", required=True, type=click.Path(exists=True), help="Path that contains all plugin files")
@click.option('-t', '--test-path', envvar="CI_PLUGIN_TEST_DIR", type=click.Path(exists=True), help="Destination used to hold the host project for testing (default: {path}/Test)")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help="Path to the engine (default: auto-discovered)")
def plugin(plugin_name, path, test_path, engine_path):
    plugin = env.Plugin(plugin_name, path)
    if test_path:
        plugin.test_path = test_path

    ue4.set_engine_root(plugin.get_short_engine_version(), engine_path)

    print("\n-- Create host project")
    create_host_project(plugin)

    result = ue4.test_plugin(plugin)
    test_report.generate(plugin)

    ue4.clear_engine_root()
    return result

def create_host_project(plugin):
    if os.path.exists(plugin.test_path):
        shutil.rmtree(plugin.test_path, ignore_errors=True)
    os.makedirs(plugin.test_path)

    # Create .uproject file
    file = open(os.path.join(plugin.test_path, 'HostProject.uproject'), 'w')
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
    host_plugin_dir = os.path.join(plugin.test_path, "Plugins", plugin.name)

    # Copy plugin into host project
    shutil.copytree(plugin.build_path, host_plugin_dir, ignore=shutil.ignore_patterns('Intermediate'))

test.add_command(plugin)

if __name__ == '__main__':
    sys.exit(test())