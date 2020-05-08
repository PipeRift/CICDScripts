import sys
import os
from os import path
import shutil

import helpers
from helpers import env, ue4


mega_root_folder = r'F:\Mega'

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


    if not path.exists(mega_root_folder):
        print("Invalid mega folder '%s'" % mega_root_folder)
        error = -1

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


    ue4.prepare(env)

    print("\n-- Create cloud folder")
    mega_folder = path.join(mega_root_folder, "Piperift", env.plugin, "Last", env.commit_ref_name)
    print(mega_folder)
    if not path.exists(mega_folder):
        os.makedirs(mega_folder)

    print("\n-- Storing files")
    try:
        shutil.copy(package_path, mega_folder)
        shutil.copy(package_path_bin, mega_folder)
    except IOError as e:
        print("Unable to copy file '%s'" % e)
        return -1
    return 0

if __name__ == '__main__':
    if env.init(sys.argv[1:]) != 0:
        sys.exit(-1)
    else:
        sys.exit(main())