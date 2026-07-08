from helpers import env, unreal, click
from helpers.util import *


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", help="Name of the project (without .uproject/.uplugin)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
def generate_project(name, path, engine_path):
    project = env.Project(name, path)
    ue = unreal.Unreal(project.get_short_engine_version(), engine_path)

    config = unreal.GenerateProjectConfig()
    config.additional_args = ["-mode=GenerateClangDatabase"]
    if ue.generate_project(project, config) != 0:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")

if __name__ == '__main__':
    generate_project()
