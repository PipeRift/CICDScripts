from helpers import env, click
from helpers.util import *
import subprocess


def format_files(files, verbose):
    if not files:
        print(f"No files to format.")  
        return

    print(f"Formatting {len(files)} files...")
    
    # Run clang-format on each file
    any_errors = False
    for file in files:
        try:
            run(["clang-format", "-style=file", "-i", str(file)])
            if verbose:
                print(f"Formatted: {file}")
        except subprocess.CalledProcessError as e:
            print(f"Error formatting {file}: {e}")
            any_errors = True
    if any_errors:
        print("-- Failed")
        sys.exit(-1)
    print("-- Succeeded")


@click.command()
@click.option('-n', '--name', envvar="CI_NAME", help="Name of the project or plugin (without .uproject/.uplugin)")
@click.option('-p', '--path', envvar="CI_PATH", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project/plugin files")
@click.option('-f', '--filters', type=str, multiple=True, envvar="CI_FILTER", help=f"{colors.OKCYAN}(default: *.h *.hpp *.c *.cpp){colors.ENDC} Glob filter of files to include")
@click.option('-v', '--verbose', is_flag=True)
def format_cli(name, path, filters, verbose):
    """Formats all source files in a project. """
    if not filters:
        filters = ("*.h", "*.hpp", "*.c", "*.cpp")

    files = set()
    try:
        plugin = env.Plugin(name, path)
        path = Path(os.path.join(plugin.path, "Source"))
        click.echo(f"{colors.WARNING}-- Formatting plugin {colors.OKGREEN}{plugin.name} {colors.WARNING}({path}){colors.ENDC}")
    except:
        try:
            project = env.Project(name, path)
            path = Path(os.path.join(project.path, "Source"))
            click.echo(f"{colors.WARNING}-- Formatting project {colors.OKGREEN}{project.name} {colors.WARNING}({path}){colors.ENDC}")
        except:
            path = Path(os.path.abspath(path) if path else os.getcwd())
            if path.is_file():
                click.echo(f"{colors.WARNING}-- Formatting file {colors.OKGREEN}{path}{colors.ENDC}")
                files.add(path)
            else:
                click.echo(f"{colors.WARNING}-- Formatting folder {colors.OKGREEN}{path}{colors.ENDC}")

    if not path.is_file():
        for ext in filters:
            files.update(path.rglob(ext))

    format_files(files, verbose)
        

if __name__ == '__main__':
    format_cli()
