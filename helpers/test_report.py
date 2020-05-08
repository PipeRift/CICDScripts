from os import path
from datetime import datetime

from .util import install
install('junit_xml')
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

def parse_test(result):
    test = result["test"]
    parse_long_name(test)
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

def operate_test(test):
    test['elapsed'] = test['final_date'] - test['start_date']

def generate_junit_tests(root_folder):
    suites = []

    for folderId in root_folder:
        test_cases = []
        folder = root_folder[folderId]

        if 'tests' in folder:
            for test in folder['tests']:
                status = test['result'];

                case = TestCase(test['name'], test['long_name'], 0, None, '\n'.join(test['events']), None, test['start_date'], status)

                if status == "Failed":
                    case.failure_message = '\n'.join(test['events'])
                test_cases.append(case)

        suite = TestSuite(folderId, test_cases)
        suites.append(suite)

    return suites


def generate(env):
    log_file = path.join(env.test_path, "Saved", "Logs", "HostProject.log")
    report_file = path.join(env.test_path, "Report.xml")

    test_folder = {}

    # Open input file in 'read' mode
    with open(log_file, "r") as file:
        test_recording = None
        tests = {}

        # Loop over each log line
        for line in file:
            result = parse(
                "[{test[start_date]:date}][{}]LogAutomationController: {log_type}: Running Automation: '{test[long_name]}' (Class Name: '{}')",
                line,
                dict(date=parse_date))

            if result is not None:
                test = parse_test(result)
                test["events"] = []
                tests[test["long_name"]] = test
                continue

            result = parse(
                "[{test[final_date]:date}][{}]LogAutomationController: {log_type}: Automation Test {test[result]:result} ({} - {test[long_name]})",
                line,
                dict(date=parse_date, result=parse_result))

            if result is not None:
                test = parse_test(result)
                tests[test["long_name"]].update(test)
                continue

            if test_recording is None:
                result = parse("[{}][{}]LogAutomationController: BeginEvents: {long_name}", line)
                if result is not None:
                    test_recording = result["long_name"]
            else:
                result = parse("[{}][{}]LogAutomationController: EndEvents: {long_name}", line)
                if result is not None:
                    test_recording = None
                    continue

                result = parse("[{}][{}]LogAutomationController: {event}", line)
                if result is None:
                    continue

                tests[test_recording]["events"].append(result["event"])

        for test in tests:
            operate_test(tests[test])
            insert_to_folders(test_folder, tests[test])

    suites = generate_junit_tests(test_folder)

    with open(report_file, "w") as dest_file:
        TestSuite.to_file(dest_file, suites, True)



#test_cases = [TestCase('Test1', 'some.class.name', 123.345, 'I am stdout!', 'I am stderr!')]
#ts = TestSuite("my test suite", test_cases)
# pretty printing is on by default but can be disabled using prettyprint=False
#print(TestSuite.to_xml_string([ts]))