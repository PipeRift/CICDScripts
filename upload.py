import sys
import os
from os import path
import shutil
import subprocess

import helpers
from helpers import env, ue4, util


def main():
    error = 0
    if env.project_path is None:
        print("Missing project path")
        error = -1
    elif not path.exists(env.project_path):
        print("Invalid project path '%s'" % env.project_path)
        error = -1
    if error != 0:
        return error


    package_path = path.join(env.build_path, env.plugin + env.compact_version + ".zip")
    package_path_bin = path.join(env.build_path, env.plugin + env.compact_version + "_Bin.zip")
    if not path.exists(package_path):
        print("Couldn't find packaged file '%s'" % package_path)
        error = -1
    if not path.exists(package_path_bin):
        print("Couldn't find packaged file '%s'" % package_path_bin)
        error = -1
    if error != 0:
        return error


    print("\n-- Prepare vault")
    vault_path = path.join(env.project_path, "Vault")
    error = PrepareVault(vault_path)
    if error != 0:
        return error

    print("\n-- Create cloud folder")
    vault_file_path = path.join(vault_path, env.plugin, "Last", env.commit_ref_name)
    if not path.exists(vault_file_path):
        os.makedirs(vault_file_path)

    print("\n-- Storing files")
    try:
        shutil.copy(package_path, vault_file_path)
        shutil.copy(package_path_bin, vault_file_path)
    except IOError as e:
        print("Unable to copy file '%s'" % e)
        return -1

    return PushFilesToVault(vault_path)


def PrepareVault(vault_path):
    vault_url = "https://gitlab.com/piperift/ci-cd/vault.git"

    try:

        # Initialize vault repository without downloading lfs files of previous builds
        subprocess.check_call(["mkdir", "Vault"], shell=True, cwd=env.project_path)
        subprocess.check_call(["git", "init"], shell=True, cwd=vault_path)
        subprocess.check_call(["git", "lfs", "install", "--skip-smudge"], shell=True, cwd=vault_path)

        subprocess.check_call(["git", "config", "user.name", "Build Bot"], shell=True, cwd=vault_path)
        subprocess.check_call(["git", "config", "user.email", "info@piperift.com"], shell=True, cwd=vault_path)

        subprocess.check_call(["git", "remote", "add", "origin", vault_url], shell=True, cwd=vault_path)
        subprocess.check_call(["git", "fetch"], shell=True, cwd=vault_path)
    except subprocess.CalledProcessError as e:
        print("Unable to prepare vault '%s'" % e)
        return -1
    return 0

def PushFilesToVault(vault_path):
    try:
        subprocess.check_call(["git", "add", "--all"], shell=True, cwd=vault_path)
        commit_message = "[" + env.plugin + "] Added packaged files (" + env.dot_version + ") \n\n Pipeline: " + env.pipeline_url
        subprocess.check_call(["git", "commit", '-m "' + commit_message + '"'], shell=True, cwd=vault_path)
        subprocess.check_call(["git", "push", "origin", "master"], shell=True, cwd=vault_path)
    except subprocess.CalledProcessError as e:
        print("Unable to push files '%s'" % e)
        return -1
    return 0


if __name__ == '__main__':
    if env.init(sys.argv[1:]) != 0:
        sys.exit(-1)
    else:
        sys.exit(main())