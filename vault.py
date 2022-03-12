import os

from helpers import env
from helpers.util import *
from helpers.vault import Vault

install('click')
import click


@click.group()
def vaultCLI():
    pass

@click.command()
@click.option('-n', '--plugin-name', envvar="CI_PLUGIN", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", required=True, type=click.Path(exists=True), help="Path that contains all plugin files")
@click.option('-v', '--vault-path', envvar="CI_PLUGIN_VAULT_DIR", type=click.Path(exists=True), help="Folder that will contain the vault (default: {path}/Vault)")
@click.option('-f', '--files-path', envvar="CI_PLUGIN_COMPRESSION_DIR", type=click.Path(exists=True), help="Folder that will contain the vault (default: {path}/Package)")
def upload(plugin_name, path, vault_path, files_path):
    plugin = env.Plugin(plugin_name, path, vault_path=vault_path)
    if not files_path:
        files_path = os.path.join(plugin.path, "Package")

    print("\n-- Clone vault")
    vault = Vault(os.path.join(env.project_path, "Vault"), env.vault_token)

    print("\n-- Copying files")
    file = os.path.join(files_path, '{}{}.zip'.format(plugin.name, plugin.get_compact_engine_version()))
    file_bin = os.path.join(files_path, '{}{}_Bin.zip'.format(plugin.name, plugin.get_compact_engine_version()))
    vault.add([file, file_bin], os.path.join('.', plugin.name, env.commit_ref_name))

    print("\n-- Uploading files")
    vault.push("[{}] Added packaged files ({}). Pipeline: {}".format(plugin.name, plugin.version, env.pipeline_url))

vaultCLI.add_command(upload)


if __name__ == '__main__':
    sys.exit(vaultCLI())