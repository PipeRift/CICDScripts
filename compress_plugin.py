import sys
import os
from os import path
import shutil

import helpers
from helpers import env, ue4


def main():
    error = 0
    if env.project_path is None:
        print("Missing project path")
        error = -1
    elif not path.exists(env.project_path):
        print("Invalid project path '%s'" % env.project_path)
        error = -1

    build_result_path = path = path.join(env.build_path, env.plugin + '_' + env.engine_version)
    if not path.exists(env.project_path):
        print("No build found at '%s'" % build_result_path)
        error = -1

    if error != 0:
        return error

    ue4.prepare(env)

    print("\n-- Clean temporal folder")
    temporal_path = path = path.join(env.build_path, env.plugin + 'Temp')
    if path.exists(temporal_path):
        shutil.rmtree(temporal_path)
    os.makedirs(temporal_path)

    print("\n-- Remove old packaged Plugin")
    zip_file     = path = path.join(env.build_path, env.plugin + '_' + env.compact_version + '.zip')
    zip_file_bin = path = path.join(env.build_path, env.plugin + '_' + env.compact_version + '_Bin.zip')
    os.remove(zip_file)
    os.remove(zip_file_bin)

    print("\n-- Cleanup Online Documentation")
    shutil.rmtree(path.join(temporal_path, 'Docs'))

    print("\n-- Copy %s Plugin" % env.dot_version)

    print("\n-- Copy Config")

    print("\n-- Compress Plugin with Binaries")

    print("\n-- Cleanup Plugin Binaries")

    print("\n-- Compress Plugin")

    return result


if __name__ == '__main__':
    if env.init(sys.argv[1:]) != 0:
        sys.exit(-1)
    else:
        sys.exit(main())