import warnings
from os import path
from datetime import datetime, timedelta

from .util import install
install('parse')

from junit_xml import TestSuite, TestCase
from parse import *


def parse_date(text):
    return datetime.strptime(text, "%Y.%m.%d-%H.%M.%S:%f")

def parse_result(text):
    return text

def parse_long_name(test):
    namespaces = test["long_name"].split('.')
    test["name"] = namespaces[-1]
    del namespaces[-1]
    test["namespaces"] = '.'.join(namespaces)

def create_test(parse_result):
    test = parse_result["test"]

    if 'start_date' not in test:
        test['start_date'] = None
    if 'finish_date' not in test:
        test['finish_date'] = None

    parse_long_name(test)
    test["result"] = "Skip"
    test["events"] = []
    return test

def insert_to_folders(root_folder, test):
        folder = root_folder
        namespaces = test["namespaces"]

        if namespaces not in folder:
            folder[namespaces] = {}
        folder = folder[namespaces]

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
                status = test['result'];

                case = TestCase(
                    test['name'],
                    test['long_name'],
                    test['elapsed'].total_seconds(),
                    ''.join(test['events']),
                    None,
                    None,
                    None,
                    status)

                if status == 'Skip':
                    case.add_skipped_info(" ")
                elif status == 'Failed':
                    case.add_failure_info(" ")

                test_cases.append(case)

        suite = TestSuite(folderId, test_cases)
        suites.append(suite)

    return suites


def generateFromEnv(env):
    log_file = path.join(env.test_path, "Saved", "Logs", "HostProject.log")
    report_file = path.join(env.test_path, "Report.xml")

    generate(log_file, report_file)

def generate(log_file, report_file):
    test_folder = {}

    # Open input file in 'read' mode
    with open(log_file, "r") as file:
        last_started_test = None
        active_test_events = None
        tests = {}

        # Loop over each log line
        for line in file:

            # Test listed
            result = parse("[{}][{}]LogAutomationCommandLine: Display: 	{test[long_name]}", line)
            if result is not None:
                test = create_test(result)
                tests[test["long_name"]] = test
                continue


            # Test started
            result = parse(
                "[{test[start_date]:date}][{}]LogAutomationController: Display: Test Started. Name={{{test[name]}}}",
                line,
                dict(date=parse_date, result=parse_result))
            if result is not None:
                last_started_test = result["test"]
                continue

            # Test completed
            result = parse(
                "[{test[finish_date]:date}][{}]LogAutomationController: Display: Test Completed. Result={{{test[result]:result}}} Name={} Path={{{test[long_name]}}}",
                line,
                dict(date=parse_date, result=parse_result))
            if result is not None:
                parsed_test = result["test"]

                if last_started_test is not None:
                    parsed_test['start_date'] = last_started_test['start_date']

                test_name = parsed_test["long_name"]
                if test_name in tests:
                    tests[test_name].update(parsed_test)
                else:
                    warnings.warn("Test {} has not been listed!", test_name)
                continue

            # Record test events
            if active_test_events is None:
                # Test Events begin
                result = parse("[{}][{}]LogAutomationController: BeginEvents: {long_name}", line)
                if result is not None:
                    active_test_events = result['long_name']
            else:
                # Test Events end
                result = parse("[{}][{}]LogAutomationController: EndEvents: {long_name}", line)
                if result is not None:
                    active_test_events = None
                    continue

                result = parse("[{}][{}]LogAutomationController: {event}", line)
                if result is not None:
                    tests[active_test_events]["events"].append(result["event"])

        for test in tests:
            set_elapsed(tests[test])
            insert_to_folders(test_folder, tests[test])

    suites = generate_junit_tests(test_folder)

    with open(report_file, "w") as dest_file:
        TestSuite.to_file(dest_file, suites, True)



#test_cases = [TestCase('Test1', 'some.class.name', 123.345, 'I am stdout!', 'I am stderr!')]
#ts = TestSuite("my test suite", test_cases)
# pretty printing is on by default but can be disabled using prettyprint=False
#print(TestSuite.to_xml_string([ts]))