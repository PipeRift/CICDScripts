import sys
import os
from helpers.util import *
from helpers import env, unreal, test_report

install('click')
import click  # NOQA


@click.group()
def test():
    pass


@click.command()
@click.option('-n', '--name', envvar="CI_PLUGIN_NAME", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", type=click.Path(exists=True), help="{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all project files")
@click.option('-b', '--build-path', envvar="CI_PROJECT_BUILD_DIR", type=click.Path(exists=True), help=f"{colors.OKCYAN}(default: <path>/Build){colors.ENDC}")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help="Path to the engine (default: auto-discovered)")
@click.option('-c', '--config', envvar="CI_PROJECT_CONFIG", help=f"{colors.OKCYAN}(default: Development){colors.ENDC} Valid: 'Debug', 'DebugGame', 'Development', 'Test' and 'Shipping'.")
@click.option('-ed', '--editor', is_flag=True, help="Should tests run in editor?")
@click.option('-rhi', '--rhi', is_flag=True, help="Should tests run with rendering? (not headless)")
@click.option('-a', '--all', is_flag=True, help="Should tests run with rendering?")
@click.option('-f', '--filter', type=click.Choice(["Engine", "Smoke", "Stress", "Perf", "Product"], case_sensitive=False), multiple=True, help="Which test filters to include. '-f Smoke -f Product' or '-t {Smoke, Product}'")
@click.option('-t', '--test', help="If provided, specific tests that should run. '-t A -t B' or '-t {A, B}'", multiple=True)
def project(name, path, build_path, engine_path, config, editor, rhi, all, filter, test):
    if not config:
        config = "Development"
    project = env.Project(name, path, build_path)
    uat = unreal.UAT(project.get_short_engine_version(), engine_path)

    print(f"-- Run tests for project {project.name}")
    uat.run_project_tests(project, all, filter, test,
                          editor, config, not rhi)


test.add_command(project)


@click.command()
@click.option('-n', '--name', envvar="CI_PLUGIN", required=True, help="Name of the plugin (without .uplugin)")
@click.option('-p', '--path', envvar="CI_PROJECT_DIR", type=click.Path(exists=True), help="{colors.OKCYAN}(default: current path){colors.ENDC} Path that contains all plugin files")
@click.option('-pt', '--test-path', envvar="CI_PLUGIN_TEST_DIR", type=click.Path(exists=True), help="Destination used to hold the host project for testing (default: {path}/Test)")
@click.option('-e', '--engine-path', envvar="CI_ENGINE_DIR", type=click.Path(exists=True), help="Path to the engine (default: auto-discovered)")
@click.option('-rhi', '--rhi', is_flag=True, help="Should tests run with rendering? (not headless)")
@click.option('-a', '--all', is_flag=True, help="Should tests run with rendering?")
@click.option('-f', '--filter', type=click.Choice(["Engine", "Smoke", "Stress", "Perf", "Product"], case_sensitive=False), multiple=True, help="Which test filters to include. '-f Smoke -f Product' or '-t {Smoke, Product}'")
@click.option('-t', '--test', help="If provided, specific tests that should run. '-t A -t B' or '-t {A, B}'", multiple=True)
def plugin(name, path, test_path, engine_path, rhi, all, filter, test):
    plugin = env.Plugin(name, path)
    uat = unreal.UAT(plugin.get_short_engine_version(), engine_path)

    if not test_path:
        test_path = os.path.join(plugin.path, 'Test')
    elif not os.path.isabs(test_path):
        test_path = os.path.join(plugin.path, test_path)

    print(f"-- Run tests for plugin {plugin.name}")
    result = uat.run_plugin_tests(
        plugin, test_path, all, filter, test, not rhi)
    return result


test.add_command(plugin)


if __name__ == '__main__':
    sys.exit(test())
