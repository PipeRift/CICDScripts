from parse import *
from helpers.junit_xml import TestSuite, TestCase
import warnings
from os import path
from datetime import datetime, timedelta

from . import env
from .util import install

install('parse')
install('six')


def parse_date(text):
    return datetime.strptime(text, "%Y.%m.%d-%H.%M.%S:%f")


def parse_result(text):
    return text


def validate_test(test):
    if 'long_name' not in test:
        test['long_name'] = None
    if 'start_date' not in test:
        test['start_date'] = None
    if 'finish_date' not in test:
        test['finish_date'] = None

    namespaces = test['long_name'].split('.')
    if len(namespaces) > 0:
        test['namespace'] = namespaces[0]
        del namespaces[0]
        test['long_name'] = '.'.join(namespaces)
        if 'name' not in test:
            test["name"] = namespaces[-1]

    if 'result' not in test:
        test["result"] = "Skip"
    if 'events' not in test:
        test["events"] = []
    return test


def find_or_add(dictionary, key, add_value=None):
    if not key in dictionary:
        dictionary[key] = add_value
    return dictionary[key]


def insert_to_folders(root_folder, test):
    folder = root_folder
    namespace = test["namespace"]

    if namespace not in folder:
        folder[namespace] = {}
    folder = folder[namespace]

    if 'tests' not in folder:
        folder['tests'] = []
    folder['tests'].append(test)


def set_elapsed(test):
    if ('start_date' in test and 'finish_date' in test) and (test['start_date'] is not None and test['finish_date'] is not None):
        test['elapsed'] = test['finish_date'] - test['start_date']
    else:
        test['elapsed'] = timedelta()


def generate_junit_tests(root_folder):
    suites = []

    for folderId in root_folder:
        test_cases = []
        folder = root_folder[folderId]

        if 'tests' in folder:
            for test in folder['tests']:
                status = test['result']

                output = '\n'.join(test['events'])

                case = TestCase(
                    test['name'],
                    test['long_name'],
                    test['elapsed'].total_seconds(),
                    None,
                    None,
                    None,
                    None,
                    status)

                if status == 'Skip':
                    case.add_skipped_info(output)
                elif status == 'Failed':
                    if not output:
                        output = ' '
                    case.add_failure_info(output)
                else:
                    case.stdout = output

                test_cases.append(case)

        suite = TestSuite(folderId, test_cases)
        suites.append(suite)

    return suites


def generate_project(project: env.Project, report_path=None):
    log_file = path.join(project.get_logs_path(), f"{project.name}.log")
    if not report_path:
        report_path = project.path
    report_file = path.join(report_path, "Report.xml")
    generate_from_log(log_file, report_file)


def generate_plugin(plugin: env.Plugin, report_path=None):
    log_file = path.join(plugin.get_logs_path(), f"{plugin.name}.log")
    if not report_path:
        report_path = plugin.path
    report_file = path.join(report_path, "Report.xml")
    generate_from_log(log_file, report_file)


def generate_from_log(log_file, report_file):
    test_folder = {}

    # Open input file in 'read' mode
    with open(log_file, "r") as file:
        active_events_test = None
        tests = {}

        # Loop over each log line
        for line in file:
            # Early out to ignore most lines
            if not "LogAutomation" in line:
                continue

            # Test listed
            result = parse(
                "[{}][{}]LogAutomationCommandLine: Display: 	{long_name}\n", line)
            if result is not None:
                long_name = result['long_name']
                find_or_add(tests, long_name, {
                            'long_name': long_name, 'events': []})
                continue

            # Test started
            result = parse(
                "[{test[start_date]:date}][{}]LogAutomationController: Display: Test Started. Name={{{test[name]}}} Path={{{test[long_name]}}}\n",
                line,
                dict(date=parse_date))
            if result is not None:
                test = find_or_add(
                    tests, result["test"]["long_name"], {'events': []})
                test.update(result["test"])
                continue

            # Test completed
            result = parse(
                "[{test[finish_date]:date}][{}]LogAutomationController: Display: Test Completed. Result={{{test[result]:result}}} Name={} Path={{{test[long_name]}}}\n",
                line,
                dict(date=parse_date, result=parse_result))
            if result is not None:
                test = find_or_add(
                    tests, result["test"]["long_name"], {'events': []})
                test.update(result["test"])
                continue

            # Record test events
            if active_events_test is None:
                # Test Events begin
                result = parse(
                    "[{}][{}]LogAutomationController: BeginEvents: {long_name}\n", line)
                if result is not None:
                    long_name = result['long_name']
                    active_events_test = find_or_add(
                        tests, long_name, {'long_name': long_name, 'events': []})
            else:
                # Test Events end
                result = parse(
                    "[{}][{}]LogAutomationController: EndEvents: {long_name}\n", line)
                if result is not None:
                    active_events_test = None
                    continue

                result = parse(
                    "[{}][{}]LogAutomationController: {event}\n", line)
                if result is not None:
                    active_events_test["events"].append(result["event"])

        for test in tests.values():
            validate_test(test)
            set_elapsed(test)
            insert_to_folders(test_folder, test)

    suites = generate_junit_tests(test_folder)

    with open(report_file, "w") as dest_file:
        TestSuite.to_file(dest_file, suites, True)
