import sys
import os
import shutil
from Scripts.helpers import unreal

from helpers.util import *
from helpers import env, test_report

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
    plugin = env.Plugin(plugin_name, path, test_path=test_path)

    unreal.override_engine_path(plugin.get_short_engine_version(), engine_path)

    print("\n-- Create host project")
    create_host_project(plugin)

    result = unreal.test_plugin(plugin)
    test_report.generate(plugin)

    unreal.clean_engine_path()
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