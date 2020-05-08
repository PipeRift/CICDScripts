import sys
import os
from os import path
import shutil

import helpers
from helpers import env, ue4, test_report


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

    ue4.prepare(env)

    print("\n-- Create host project")
    CreateHostProject()

    result = ue4.test(env)

    test_report.generate(env)

    return result


def CreateHostProject():
    if path.exists(env.test_path):
        shutil.rmtree(env.test_path, ignore_errors=True)
    os.makedirs(env.test_path)

    # Create .uproject file
    file = open(path.join(env.test_path, 'HostProject.uproject'), 'w')
    file.write('{ \
        "FileVersion": 3, \
        "Plugins": \
        [ \
            { \
                "Name": "' + env.plugin + '", \
                "Enabled": true \
            } \
        ] \
    }')
    file.close()

	# Get the plugin directory in the host project, and copy all the files in
    host_plugin_dir = path.join(env.test_path, "Plugins", env.plugin)

	# Get the plugin directory in the host project, and copy all the files in
    build_plugin_dir = path.join(env.build_path, env.plugin + "_" + env.compact_version)

    #Ignore Intermediates, Docs and Scripts folders
    to_exclude = [path.join(build_plugin_dir, "Intermediates")]
    def IgnoredPaths(path, filenames):
        ret = []
        for filename in filenames:
            if os.path.join(path, filename) in to_exclude:
                ret.append(filename)
        return ret

    # Copy plugin
    shutil.copytree(build_plugin_dir, host_plugin_dir, ignore=IgnoredPaths)

if __name__ == '__main__':
    if env.init(sys.argv[1:]) != 0:
        sys.exit(-1)
    else:
        sys.exit(main())