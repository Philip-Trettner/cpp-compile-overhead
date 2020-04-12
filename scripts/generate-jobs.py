#!/usr/bin/env python3

import os
import argparse
import platform
import json

parser = argparse.ArgumentParser(
    description="Generate a tasks for C++ compile-health analyzer")
parser.add_argument("file", metavar="F",
                    help="file to store the schedule in (e.g. jobs.json)")
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
    compiler_name = None

    def __init__(self):
        self.args = []

    def make_args(self):
        return self.args + ["-std=c++{}".format(self.cpp)]


def generate_configs():

    if is_windows:
        assert False, "TODO: implement me"

    elif is_linux:
        for cc in [
            ['Clang 6', '/usr/bin/clang++-6'],
            ['Clang 7', '/usr/bin/clang++-7'],
            ['Clang 8', '/usr/bin/clang++-8'],
            ['Clang 9', '/usr/bin/clang++-9'],
            ['GCC 7', '/usr/bin/g++-7'],
            ['GCC 8', '/usr/bin/g++-8'],
            ['GCC 9', '/usr/bin/g++-9'],
        ]:
            if not os.path.exists(cc[1]):
                continue

            for cpp in [11, 14, 17]:
                for opt in ['-O0', '-O2']:
                    c = Config()
                    c.cpp = cpp
                    c.args.append(opt)
                    c.compiler = cc[1]
                    c.compiler_name = cc[0]
                    yield c

    else:
        assert False, "unknown platform"


all_configs = list(generate_configs())
since_cpp14_configs = [c for c in all_configs if c.cpp >= 14]
since_cpp17_configs = [c for c in all_configs if c.cpp >= 17]


def add(project, version, name, file, variant, configs):
    for c in configs:
        jobs.append({
            "project": project,
            "version": version,
            "name": name,
            "file": file,
            "variant": variant,
            "args": c.make_args(),
            "compiler": c.compiler,
            "compiler_name": c.compiler_name,
        })
        if args.verbose:
            print("added {}".format(jobs[-1]))

# ===============================================================
# Projects
# ===============================================================


# ===============================================================
# c++ std
for h in [
    "cstdlib",
    "csignal",
    "csetjmp",
    "cstdarg",
    "typeinfo",
    "typeindex",
    "type_traits",
    "bitset",
    "functional",
    "utility",
    "ctime",
    "chrono",
    "cstddef",
    "initializer_list",
    "tuple",
    "new",
    "memory",
    "scoped_allocator",
    "climits",
    "cfloat",
    "cstdint",
    "cinttypes",
    "limits",
    "exception",
    "stdexcept",
    "cassert",
    "system_error",
    "cerrno",
    "cctype",
    "cwctype",
    "cstring",
    "cwchar",
    "cuchar",
    "string",
    "array",
    "vector",
    "deque",
    "list",
    "forward_list",
    "set",
    "map",
    "unordered_set",
    "unordered_map",
    "stack",
    "queue",
    "iterator",
    "algorithm",
    "cmath",
    "complex",
    "valarray",
    "random",
    "numeric",
    "ratio",
    "cfenv",
    "iosfwd",
    "ios",
    "istream",
    "ostream",
    "iostream",
    "fstream",
    "sstream",
    "strstream",
    "iomanip",
    "streambuf",
    "cstdio",
    "locale",
    "clocale",
    "regex",
    "atomic",
    "thread",
    "mutex",
    "shared_mutex",
    "future",
    "condition_variable",
]:
    add("C++ Standard Library", "", "<" + h + ">", h, "", all_configs)

for h in [
    "shared_mutex",
]:
    add("C++ Standard Library", "", "<" + h + ">", h, "", since_cpp14_configs)

for h in [
    "any",
    "optional",
    "variant",
    "memory_resource",
    "string_view",
    "charconv",
    "execution",
    "filesystem",
]:
    add("C++ Standard Library", "", "<" + h + ">", h, "", since_cpp17_configs)


# ===============================================================
# finalize

with open(args.file, "w") as f:
    json.dump(jobs, f, indent=4)
