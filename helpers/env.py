from os import environ, path

# Normally, the branch of the commit
commit_ref_name = environ.get('CI_COMMIT_REF_NAME')
if commit_ref_name is None:
    commit_ref_name = "no_branch"



def init(args):
    # Plugin
    global plugin
    if len(args) > 0 and args[0] != None:
        plugin = args[0]
    else:
        plugin = environ.get('plugin')

    # Versions
    global engine_version
    if len(args) > 1 and args[1] != None:
        engine_version = args[1]
    else:
        engine_version = environ.get('engine_version')

    global dot_version, compact_version
    if engine_version != None:
        dot_version = "4." + engine_version
        compact_version = "4" + engine_version
    else:
        dot_version = compact_version = None

    # Engine
    global engine_path
    if dot_version is not None:
        engine_path = path.join(environ.get('ProgramW6432'), "Epic Games", "UE_" + dot_version)

    # Project
    global project_path, build_path, test_path
    if len(args) > 2 and args[2] != None:
        project_path = args[2]
    else:
        project_path = environ.get('CI_PROJECT_DIR')

    if project_path != None:
        build_path = path.join(project_path, 'Build')
        test_path = path.join(project_path, 'Test')
    else:
        build_path = test_path = None

    # Pipeline
    global pipeline_url
    pipeline_url = environ.get('CI_PIPELINE_URL')

    if plugin is None or engine_version is None:
        print("Missing environment variables 'plugin' or 'engine_version'")
        return -1
    return 0