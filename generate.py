from helpers import env, unreal, click
from helpers.util import *


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", help="Name of the project (without .uproject/.uplugin)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: auto-discovered){colors.ENDC}")
@click.option('-i', '--ide', envvar="CI_IDE", type=click.Choice(unreal.IDE, case_sensitive=False), help=f"{colors.OKCYAN}(default: VisualStudio){colors.ENDC}")
def generate_project(name, path, engine_path, ide):
    """Generates project files for the desired IDE. """
    if not ide:
        ide = unreal.IDE.VisualStudio

    project = env.Project(name, path)
    ue = unreal.Unreal.from_project(project, engine_path)

    config = unreal.GenerateProjectConfig()
    config.ide = ide

    print("-- Generating Project Files")
    if ue.generate_project(project, config) != 0:
        print("-- Failed to generate project files")
        sys.exit(-1)

    print("-- Generating Clang database")
    if ue.generate_clang_db(project, config) != 0:
        print("-- Failed to generate clang database")
        sys.exit(-1)

    print("-- Succeeded")

if __name__ == '__main__':
    generate_project()
