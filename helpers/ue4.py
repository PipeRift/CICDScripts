import os
import subprocess
from .util import install

ue4cli_is_installed = False
manager = None

def setup_cli():
    global ue4cli_is_installed, manager
    if ue4cli_is_installed:
        return

    install('ue4cli')
    from ue4cli import UnrealManagerFactory, UnrealManagerException
    manager = UnrealManagerFactory.create()
    ue4cli_is_installed = True

def set_engine_root(version, override_path=None):
    setup_cli()
    print("-- Finding engine root for version {}".format(version))
    global overrided_engine_path
    cli_version = manager.getEngineVersion('short')
    overrided_engine_path = False

    if override_path:
        manager.setEngineRootOverride(override_path)
        overrided_engine_path = True
    # if CLI is set to an engine which doesn't match plugin's version, we try to find it
    elif cli_version and not version.startswith(cli_version):
        manager.setEngineRootOverride(
            os.path.join(os.environ.get('ProgramW6432'), "Epic Games", "UE_{}".format(version))
        )
        overrided_engine_path = True

    return manager.getEngineVersion() != None

def clean_engine_root():
    setup_cli()
    global overrided_engine_path
    if overrided_engine_path:
        manager.clearEngineRootOverride()

def build_plugin(plugin):
    setup_cli()
    try:
        manager.runUAT(['BuildPlugin',
            '-Plugin={}'.format(plugin.upluginFile),
            '-Package={}'.format(plugin.build_path)])
    except Exception as e:
        return 1
    return 0

def test_plugin(plugin):
    setup_cli()
    last_cwd = os.getcwd()
    os.chdir(plugin.test_path)

    print("-- Run tests")
    # We cant use the manager directly because it manually exits
    result = subprocess.call(["ue4", "test", plugin.name], shell=True)

    print("-- Succeeded" if result == 0 else "-- Failed")
    os.chdir(last_cwd)
    return result
