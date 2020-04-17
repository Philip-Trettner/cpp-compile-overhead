#!/usr/bin/env python3

import os
import subprocess
import argparse

parser = argparse.ArgumentParser(
    description="Generate data.js for C++ compile-health analyzer")
parser.add_argument("dir", metavar="D",
                    help="directory to work in")
parser.add_argument("--clear", help="clears cache if set", action="store_true")
parser.add_argument("-c", "--configs", type=int,
                    help="only generate a limited number of configs")
parser.add_argument("-p", "--project",
                    help="only build a specific project (e.g. -p picojson)")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")

args = parser.parse_args()

assert os.path.exists(args.dir), "directory must exist"

jobs_file = os.path.join(args.dir, "jobs.json")
data_file = os.path.join(args.dir, "compile-health-data.json")
cache_file = os.path.join(args.dir, "job-cache.json")

if args.clear and os.path.exists(cache_file):
    with open(cache_file, "w") as f:
        f.write("{}")

verbose_args = []
if args.verbose:
    verbose_args.append("-v")

# generate jobs
extra_args = []
if args.project:
    extra_args += ["-p", args.project]
if args.configs:
    extra_args += ["-c", str(args.configs)]
subprocess.check_call(
    ["python3", "scripts/generate-jobs.py", "-d", args.dir, jobs_file] + extra_args + verbose_args)

# execute jobs
subprocess.check_call(["python3", "scripts/execute-jobs.py", "-v",
                       "-d", args.dir, "-c", cache_file, jobs_file, data_file] + verbose_args)

print("generated {} kB of json data".format(
    int(os.path.getsize(data_file) / 1024.)))
# print("generated {} kB of json data (zipped)".format(int(os.path.getsize(data_file + ".gz") / 1024.)))
