#!/usr/bin/env python3

import os
import subprocess
import argparse

parser = argparse.ArgumentParser(
    description="Generate data.js for C++ compile-health analyzer")
parser.add_argument("dir", metavar="D",
                    help="directory to work in")
parser.add_argument("--clear", help="clears cache if set", action="store_true")

args = parser.parse_args()

assert os.path.exists(args.dir), "directory must exist"

jobs_file = os.path.join(args.dir, "jobs.json")
data_file = os.path.join(args.dir, "compile-health-data.json")
cache_file = os.path.join(args.dir, "job-cache.json")

if args.clear and os.path.exists(cache_file):
    with open(cache_file, "w") as f:
        f.write("{}")

# generate jobs
subprocess.check_call(
    ["python3", "scripts/generate-jobs.py", jobs_file])

# execute jobs
subprocess.check_call(["python3", "scripts/execute-jobs.py", "-v",
                       "-d", args.dir, "-c", cache_file, jobs_file, data_file])
