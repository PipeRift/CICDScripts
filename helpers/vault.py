import os
import shutil
import subprocess

from . import util


class VaultError(Exception):
    pass

class Vault(object):
    path = None

    def __init__(self, path, token):
        self.path = path

        # Clone vault repository
        vault_url = "https://oauth2:" + token + "@gitlab.com/piperift/ci-cd/vault.git"

        # Make sure the folder is empty
        util.create_or_empty(path)

        try:
            # Clone vault repository without downloading all lfs files of previous builds
            subprocess.check_call(["git", "init"], shell=True, cwd=path)
            subprocess.check_call(["git", "lfs", "install", "--skip-smudge"], shell=True, cwd=path)

            subprocess.check_call(["git", "config", "user.name", "Build Bot"], shell=True, cwd=path)
            subprocess.check_call(["git", "config", "user.email", "info@piperift.com"], shell=True, cwd=path)

            subprocess.check_call(["git", "remote", "add", "origin", vault_url], shell=True, cwd=path)
            subprocess.check_call(["git", "fetch"], shell=True, cwd=path)
            subprocess.check_call(["git", "checkout", "master"], shell=True, cwd=path)
        except subprocess.CalledProcessError as e:
            raise VaultError("Unable to prepare vault '%s'" % e)

    def add(self, files, relative_path):
        vault_file = os.path.join(self.path, relative_path)
        if not os.path.exists(vault_file):
            os.makedirs(vault_file)

        try:
            for file in files:
                if not os.path.exists(file):
                    raise VaultError("Couldn't find file '%s'" % file)

                shutil.copy(file, vault_file)
        except IOError as e:
            raise VaultError("Unable to copy file '%s'" % e)

        subprocess.check_call(["git", "add", "--all"], shell=True, cwd=self.path)

    def push(self, message):
        try:
            subprocess.check_call(["git", "commit", "-m", message], shell=True, cwd=self.path)
            subprocess.check_call(["git", "push", "origin", "master"], shell=True, cwd=self.path)
        except subprocess.CalledProcessError as e:
            raise VaultError("Unable to push files to vault '%s'" % e)
