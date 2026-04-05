
import os
import pathlib
import json


# Normally, the branch of the commit
commit_ref_name = os.environ.get('CI_COMMIT_REF_NAME')
if commit_ref_name is None:
    commit_ref_name = "no_branch"

pipeline_url = os.environ.get('CI_PIPELINE_URL')
vault_token = os.environ.get('vault_token')


class InvalidProjectError(Exception):
    pass


class Project(object):
    name = None
    path = None
    uproject_file = None
    json = None

    test_path = None
    build_path = None
    vault_path = None

    def __init__(self, name, path, build_path=None, test_path=None, vault_path=None):
        self.name = name
        self.path = os.path.abspath(path) if path else os.getcwd()
        self.uproject_file = os.path.join(
            self.path, f"{name}.uproject")

        if not os.path.isfile(self.uproject_file):
            raise InvalidProjectError("Project '{}' not found.\n.uproject file is missing ({}).".format(
                self.name, self.uproject_file))

        with open(self.uproject_file) as json_file:
            self.json = json.load(json_file)

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
        return self.json['VersionName']

    def get_engine_version(self):
        return self.json['EngineAssociation']

    def get_short_engine_version(self):
        full = self.get_engine_version()
        return '.'.join(full.split('.')[:2]) if full else None

    def get_compact_engine_version(self):
        full = self.get_engine_version()
        return ''.join(full.split('.')[:2]) if full else None

    def get_logs_path(self):
        return os.path.join(self.path, "Saved", "Logs")


class InvalidPluginError(Exception):
    pass


class Plugin(object):
    name = None
    path = None
    uplugin_file = None
    json = None

    build_path = None
    vault_path = None

    def __init__(self, name, path, build_path=None, vault_path=None):
        self.name = name
        self.path = os.path.abspath(path) if path else os.getcwd()
        self.uplugin_file = pathlib.Path(
            self.path, '{}.uplugin'.format(self.name))

        if not os.path.isfile(self.uplugin_file):
            raise InvalidPluginError("Plugin '{}' not found.\n.uplugin file is missing ({}).".format(
                self.name, self.uplugin_file))

        with open(self.uplugin_file) as json_file:
            self.json = json.load(json_file)

        self.build_path = os.path.join(self.path, 'Build')
        self.vault_path = os.path.join(self.path, 'Vault')
        if build_path:
            if os.path.isabs(build_path):
                self.build_path = build_path
            else:
                self.build_path = os.path.join(self.path, build_path)
        if vault_path:
            if os.path.isabs(vault_path):
                self.vault_path = vault_path
            else:
                self.vault_path = os.path.join(self.path, vault_path)

    def get_version(self):
        return self.json['VersionName']

    def get_engine_version(self):
        return self.json['EngineVersion']

    def get_short_engine_version(self):
        full = self.get_engine_version()
        return '.'.join(full.split('.')[:2]) if full else None

    def get_compact_engine_version(self):
        full = self.get_engine_version()
        return ''.join(full.split('.')[:2]) if full else None

    def get_logs_path(self):
        return f"{self.path}/Saved/Logs"
