import os

from helpers import env
from helpers.util import *
from helpers.vault import Vault

install('click')
import click  # NOQA


@click.group()
def vaultCLI():
    pass


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", required=True, help="Name of the plugin or project (without .uplugin/.uproject)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(), help="Path that contains all plugin/project files")
@click.option('-z', '--zip-path', envvar="CI_ZIP_PATH", type=click.Path(exists=True), help="Folder that will contain the vault (default: {path}/Package)")
@click.option('-v', '--vault-path', envvar="CI_VAULT_PATH", type=click.Path(exists=True), help="Folder that will contain the vault (default: {path}/Vault)")
def upload(plugin_name, path, zip_path, vault_path):
    plugin = env.Plugin(plugin_name, path, vault_path=vault_path)

    if not zip_path:
        zip_path = os.path.join(plugin.path, "Package")

    if not os.path.isabs(zip_path):
        zip_path = os.path.abspath(zip_path)

    print("\n-- Clone vault")
    vault = Vault(os.path.join(env.project_path, "Vault"), env.vault_token)

    print("\n-- Copying files")
    file = os.path.join(zip_path, f'{plugin.name}_v{plugin.get_version()}_{plugin.get_short_engine_version()}.zip')
    file_bin = os.path.join(zip_path, f'{plugin.name}_v{plugin.get_version()}_{plugin.get_short_engine_version()}_Bin.zip')
    vault.add([file, file_bin], os.path.join(
        '.', plugin.name, env.commit_ref_name))

    print("\n-- Uploading files")
    vault.push(f"[{plugin.name}] Added packaged files (v{plugin.get_version()} UE{plugin.get_short_engine_version()}). Pipeline: {env.pipeline_url}")


vaultCLI.add_command(upload)


if __name__ == '__main__':
    sys.exit(vaultCLI())
