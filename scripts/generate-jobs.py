#!/usr/bin/env python3

import os
import argparse
import platform
import json

parser = argparse.ArgumentParser(description="Generate a tasks for C++ compile-health analyzer")
parser.add_argument("file", metavar="F", help="file to store the schedule in (e.g. jobs.json)")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")

args = parser.parse_args()

# ===============================================================
# framework

is_windows = any(platform.win32_ver())
is_linux = not is_windows

jobs = []

class Config:
    cpp = None
    args = None
    compiler = None

    def __init__(self):
        self.args = []

    def make_args(self):
        return self.args + ["-std=c++{}".format(self.cpp)]

def generate_configs():

    if is_windows:
        assert False, "TODO: implement me"

    elif is_linux:
        for compiler in [
            '/usr/bin/clang++-6',
            '/usr/bin/clang++-7',
            '/usr/bin/clang++-8',
            '/usr/bin/clang++-9',
            '/usr/bin/g++-7',
            '/usr/bin/g++-8',
            '/usr/bin/g++-9',
        ]:
            if not os.path.exists(compiler):
                continue

            for opt in ['-O0', '-O2']:
                for cpp in [11, 14, 17]:
                    c = Config()
                    c.cpp = cpp
                    c.args.append(opt)
                    c.compiler = compiler
                    yield c

    else:
        assert False, "unkown platform"

all_configs = generate_configs()

def add(project, version, name, file, variant, configs):
    for c in configs:
        jobs.append({
            "project": project,
            "version": version,
            "name": name,
            "file": file,
            "variant": variant,
            "args": c.make_args(),
            "compiler": c.compiler
        })

# ===============================================================
# Projects
# ===============================================================

# std
for h in [
    "vector",
    "map"
]:
    add("std", "", "<" + h + ">", h, "", all_configs)



# ===============================================================
# finalize

with open(args.file, "w") as f:
    json.dump(jobs, f, indent=4)
