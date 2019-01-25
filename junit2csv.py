#!/usr/bin/env python

from __future__ import print_function
from collections import OrderedDict
import sys
import os
import csv

import xmltodict

def parse_junit(unit, prefix):
    test = {}
    test_cases = unit['testsuite']['testcase']
    if not isinstance(test_cases, list):
        test_cases = [test_cases]
    for x in test_cases:
        classname = x['@classname']
        name = x['@name']
        if 'skipped' in x:
            continue
        passed = 'failure' not in x
        test_cases[(prefix, classname, name)] = passed

    return test_cases

def merge_junit(a, b):
    merged = {}
    for (k, v) in a.iteritems():
        merged[k] = a.get(k, False) or b.get(k, False)

    for (k, v) in b.iteritems():
        merged[k] = a.get(k, False) or b.get(k, False)
    return merged

def run():
    junits = OrderedDict()

    for filepath in sys.stdin.read().splitlines():
        with open(filepath) as fd:
            try:
                (path, filename) = os.path.split(filepath)
                junits[filepath] = parse_junit(xmltodict.parse(fd), filename)
            except Exception:
                print("parse error:", filepath, file=sys.stderr)


    merged = OrderedDict()
    for x in junits.keys():
        (d, f) = os.path.split(x)
        merged[d] = merge_junit(merged.get(d, {}), junits[x])

    junits = merged
    tests = set()
    for junit in junits.values():
        for k in junit.keys():
            tests.add(k)


    testnames = sorted(list(tests))

    writer = csv.writer(sys.stdout)

    header = ["filename"]
    header.extend([x[0]+'/'+x[1]+'/'+x[2] for x in testnames])
    writer.writerow(header)

    for (f, t) in junits.iteritems():
        row = [f]
        row.extend([1 if t.get(x, False) else 0 for x in testnames])
        writer.writerow(row)

if __name__ == "__main__":
    run()
