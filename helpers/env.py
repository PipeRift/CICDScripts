
import os
import pathlib
import json


# Normally, the branch of the commit
commit_ref_name = os.environ.get('CI_COMMIT_REF_NAME')
if commit_ref_name is None:
    commit_ref_name = "no_branch"

pipeline_url = os.environ.get('CI_PIPELINE_URL')
vault_token = os.environ.get('vault_token')


class InvalidPluginError(Exception):
    pass

class Plugin(object):
    name = None
    uplugin = None
    uplugin_file = None
    path = None

    test_path = None
    build_path = None
    vault_path = None
    package_path = None

    def __init__(self, name, path, build_path = None, test_path = None):
        self.name = name
        self.path = os.path.abspath(path)
        self.upluginFile = pathlib.Path(self.path, '{}.uplugin'.format(self.name))

        if not os.path.isfile(self.upluginFile):
            raise InvalidPluginError("Plugin '{}' not found.\n.uplugin file is missing ({}).".format(self.name, self.upluginFile))

        with open(self.upluginFile) as json_file:
            self.uplugin = json.load(json_file)

        self.build_path = os.path.join(self.path, 'Build')
        self.test_path = os.path.join(self.path, 'Test')
        self.vault_path = os.path.join(self.path, 'Vault')

        if build_path:
            if os.path.isabs(build_path):
                self.build_path = build_path
            else:
                self.build_path = os.path.join(self.path, build_path)
        if test_path:
            if os.path.isabs(test_path):
                self.test_path = test_path
            else:
                self.test_path = os.path.join(self.path, test_path)
        if vault_path:
            if os.path.isabs(vault_path):
                self.vault_path = vault_path
            else:
                self.vault_path = os.path.join(self.path, vault_path)

    def get_version(self):
        return self.uplugin['VersionName']

    def get_engine_version(self):
        return self.uplugin['EngineVersion']

    def get_short_engine_version(self):
        full = self.get_engine_version()
        return '.'.join(full.split('.')[:2]) if full else None

    def get_compact_engine_version(self):
        full = self.get_engine_version()
        return ''.join(full.split('.')[:2]) if full else None

def init(_plugin, _path, _engine_version):
    global plugin
    plugin = _plugin

    global path
    path = _path

    global engine_version
    engine_version = _engine_version

    # Versions
    global dot_version, compact_version
    if engine_version != None:
        dot_version = "4." + engine_version
        compact_version = "4" + engine_version
    else:
        dot_version = compact_version = None

    # Engine
    global engine_path
    if dot_version is not None:
        engine_path = os.path.join(os.environ.get('ProgramW6432'), "Epic Games", "UE_" + dot_version)


    global build_path, test_path
    if path != None:
        build_path = os.path.join(path, 'Build')
        test_path = os.path.join(path, 'Test')
    else:
        build_path = test_path = None

    # Pipeline
    global pipeline_url
    pipeline_url = os.environ.get('CI_PIPELINE_URL')
    global vault_token
    vault_token = os.environ.get('vault_token')

    if plugin is None or engine_version is None:
        print("Missing environment variables 'plugin' or 'engine_version'")
        return -1
    return 0

def init(args): # args version of init
    plugin = None
    if len(args) > 0 and args[0] != None:
        plugin = args[0]
    else:
        plugin = os.environ.get('plugin')

    engine_version = None
    if len(args) > 1 and args[1] != None:
        engine_version = args[1]
    else:
        engine_version = os.environ.get('engine_version')

    path = None
    if len(args) > 2 and args[2] != None:
        path = args[2]
    else:
        path = os.environ.get('CI_PROJECT_DIR')

    init(plugin, path, engine_version)