import sys
import os
import shutil

from helpers.util import *
from helpers import env

install('click')
import click


@click.group()
def compress():
    pass

@click.command()
@click.option('-n', '--plugin-name', envvar="CI_PLUGIN", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", required=True, type=click.Path(exists=True), help="Path that contains all plugin files")
@click.option('-b', '--build-path', envvar="CI_PLUGIN_BUILD_DIR", type=click.Path(exists=True), help="Destination of the packaged plugin (default: {path}/Build)")
@click.option('-d', '--destination', envvar="CI_PLUGIN_COMPRESSION_DIR", type=click.Path(exists=True), help="Folder that will contain the vault (default: {path}/Temp)")
def plugin(plugin_name, path, build_path, destination):
    if not os.path.isdir(path):
        click.echo("Path is not a folder or it doesn't exist ('{}')".format(path))
        return -1

    plugin = env.Plugin(plugin_name, path)
    if build_path:
        plugin.build_path = build_path
    if not destination:
        destination = os.path.join(plugin.path, "Temp")

    temp_path = os.path.join(destination, plugin.name)
    temp_path_rel = os.path.join('.', plugin.name)

    install('py7zr')
    import py7zr

    print("Clean destination folder")
    remove(temp_path)
    if not os.path.exists(path):
        os.makedirs(destination)

    print("Remove old packaged Plugin")
    file = os.path.join(destination, '{}{}.zip'.format(plugin.name, plugin.get_compact_engine_version()))
    file_bin = os.path.join(destination, '{}{}_Bin.zip'.format(plugin.name, plugin.get_compact_engine_version()))
    remove(file)
    remove(file_bin)

    print("Copy built plugin")
    shutil.copytree(plugin.build_path, temp_path,
        ignore=shutil.ignore_patterns('Intermediate', 'Docs', 'Build', 'Vault'))

    print("Cleanup Online Documentation")
    docs_path = os.path.join(temp_path, 'Docs')
    if os.path.exists(docs_path):
        shutil.rmtree(docs_path)

    print("Copy Config")
    shutil.copytree(os.path.join(plugin.path, 'Config'), os.path.join(temp_path, 'Config'))

    print("Compress Plugin with Binaries")
    os.chdir(destination)
    with py7zr.SevenZipFile(file_bin, 'w') as f:
        f.writeall(temp_path_rel)

    print("Cleanup Plugin Binaries")
    shutil.rmtree(os.path.join(temp_path, 'Binaries'))

    print("Compress Plugin without Binaries")
    os.chdir(destination)
    with py7zr.SevenZipFile(file, 'w') as f:
        f.writeall(temp_path_rel, 'base')

    print("Clean temp")
    remove(temp_path)

    return 0

compress.add_command(plugin)

if __name__ == '__main__':
    sys.exit(compress())