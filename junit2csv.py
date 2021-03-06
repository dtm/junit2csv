#!/usr/bin/env python

from __future__ import print_function
from collections import OrderedDict
import sys
import os
import csv
import getopt

import xmltodict

def parse_junit(unit, prefix, timings=False):
    test = {}
    test_cases = unit['testsuite']['testcase']
    test_states = {}
    if not isinstance(test_cases, list):
        test_cases = [test_cases]
    for x in test_cases:
        classname = x[u'@classname']
        name = x[u'@name']
        if 'skipped' in x:
            continue
        value = None
        if timings:
            value = x['@time']
        else:
            value = 'failure' not in x
        test_states[(prefix, classname, name)] = value

    return test_states

def merge_junit(a, b):
    merged = {}
    for (k, v) in a.items():
        merged[k] = a.get(k, False) or b.get(k, False)

    for (k, v) in b.items():
        merged[k] = a.get(k, False) or b.get(k, False)
    return merged

def test_key_to_header(x):
    return x[0]+'/'+x[1]+'/'+x[2]

def run(ignore=[], timings=False):
    junits = OrderedDict()

    for filepath in sys.stdin.read().splitlines():
        with open(filepath, "rb") as fd:
            try:
                (path, filename) = os.path.split(filepath)
                junits[filepath] = parse_junit(xmltodict.parse(fd), filename, timings=timings)
            except Exception as e:
                print("parse error:", filepath, e, file=sys.stderr)

    merged = OrderedDict()
    for x in junits.keys():
        (d, f) = os.path.split(x)
        merged[d] = merge_junit(merged.get(d, {}), junits[x])

    junits = merged
    tests = set()
    for junit in junits.values():
        for k in junit.keys():
            tests.add(k)

    testnames = [x for x in sorted(list(tests)) if (test_key_to_header(x) not in ignore)]

    writer = csv.writer(sys.stdout)

    header = ["filename"]
    header.extend([test_key_to_header(x) for x in testnames])
    writer.writerow(header)

    for (f, t) in junits.items():
        def to_output(x):
            if isinstance(x, bool):
                return 1 if x else 0
            return x
        row = [f]
        row.extend(map(to_output, [t.get(x, False) for x in testnames]))
        writer.writerow(row)

def usage():
    print("Usage: %s [OPTION]..." % (sys.argv[0]))
    print("")
    print("-t, --timings            Extract timings instead of passes/failures")
    print("-x, --exclude=testname   Exclude a test from the output")
    print("")

if __name__ == "__main__":
    try:
        optlist, args = getopt.getopt(sys.argv[1:], "hx:t", ["help", "exclude=", "timings"])
    except getopt.GetoptError as err:
        usage()
        sys.exit(2)

    ignores = []
    timings = False
    for o, a in optlist:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-t", "--timings"):
            timings = True
        elif o in ("-x", "--exclude"):
            ignores.append(a)

    run(ignore=ignores, timings=timings)
