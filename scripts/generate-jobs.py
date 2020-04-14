#!/usr/bin/env python3

import glob
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

def debug_print(s):
    if args.verbose:
        print(s)

# ===============================================================
# framework

is_windows = any(platform.win32_ver())
is_linux = not is_windows


class Config:
    cpp = None
    args = None
    compiler = None
    compiler_name = None
    variant = None

    def __init__(self):
        self.args = []

    def make_args(self):
        return ["-std=c++{}".format(self.cpp)] + self.args


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
                for variant in [
                    ["Debug", ['-O0', '-g']],
                    ["RelWithDebInfo", ['-O2', '-g', '-DNDEBUG']],
                    ["Release", ['-O3', '-DNDEBUG']],
                ]:
                    c = Config()
                    c.cpp = cpp
                    c.args = variant[1] + ["-march=skylake"]
                    c.variant = variant[0]
                    c.compiler = cc[1]
                    c.compiler_name = cc[0]
                    yield c

    else:
        assert False, "unknown platform"


all_configs = list(generate_configs())
since_cpp14_configs = [c for c in all_configs if c.cpp >= 14]
since_cpp17_configs = [c for c in all_configs if c.cpp >= 17]

project_list = []
project_jobs = {}


def add(category, project, project_url, url, version, name, file, configs):
    if project not in project_jobs:
        project_list.append(project)
        project_jobs[project] = []
    for c in configs:
        job = {
            "category": category,
            "project": project,
            "project_url": project_url,
            "url": url,
            "version": version,
            "name": name,
            "file": file,
            "variant": c.variant,
            "args": c.make_args(),
            "cpp": c.cpp,
            "compiler": c.compiler,
            "compiler_name": c.compiler_name,
        }
        project_jobs[project].append(job)
        if args.verbose:
            print("added {}".format(job))

# ===============================================================
# Projects
# ===============================================================


# ===============================================================
# c++ std

url_cpp = "https://en.cppreference.com/w/cpp/header"

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
    # "strstream", # deprecated
    "iomanip",
    "streambuf",
    "cstdio",
    "locale",
    "clocale",
    "regex",
    "atomic",
    "thread",
    "mutex",
    "future",
    "condition_variable",
]:
    add("Standard Library", "C++ Standard Library", url_cpp, url_cpp + "/" + h, "", "<" + h + ">", h, all_configs)

for h in [
    "shared_mutex",
]:
    add("Standard Library", "C++ Standard Library", url_cpp, url_cpp + "/" + h, "", "<" + h + ">", h, since_cpp14_configs)

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
    for c in since_cpp17_configs:
        if h in ["memory_resource", "execution"] and "clang" in c.compiler:
            continue
        if c.compiler.endswith("g++-7") and h == "filesystem":
            continue
        if (c.compiler.endswith("g++-7") or c.compiler.endswith("g++-8")) and h in ["memory_resource", "charconv", "execution"]:
            continue

        add("Standard Library", "C++ Standard Library", url_cpp, url_cpp + "/" + h, "", "<" + h + ">", h, [c])


# ===============================================================
# c std

url_c = "https://en.cppreference.com/w/c/header"

for h in [
    "assert.h",
    "complex.h",
    "ctype.h",
    "errno.h",
    "fenv.h",
    "float.h",
    "inttypes.h",
    "iso646.h",
    "limits.h",
    "locale.h",
    "math.h",
    "setjmp.h",
    "signal.h",
    # C11: "stdalign.h",
    "stdarg.h",
    # C11: "stdatomic.h",
    "stdbool.h",
    "stddef.h",
    "stdint.h",
    "stdio.h",
    "stdlib.h",
    # C11: "stdnoreturn.h",
    "string.h",
    "tgmath.h",
    # C11: "threads.h",
    "time.h",
    # C11: "uchar.h",
    "wchar.h",
    "wctype.h",
]:
    add("Standard Library", "C Standard Library", url_c, None, "", "<" + h + ">", h, all_configs)


# ===============================================================
# libs

debug_print("parsing libraries")

for cat in os.listdir("libs"):
    catpath = "libs/" + cat
    if not os.path.isdir(catpath):
        continue

    debug_print("  " + catpath)

    for lib in os.listdir(catpath):
        libpath = catpath + "/" + lib
        if not os.path.isdir(libpath):
            continue

        debug_print("    " + libpath)

        cfgpath = libpath + "/project.json"
        assert os.path.exists(cfgpath), "no config found in " + cfgpath
        with open(cfgpath, "r") as f:
            cfg = json.load(f)
        assert "url" in cfg, "project.json needs at least an URL"

        for v in os.listdir(libpath):
            vpath = libpath + "/" + v
            if not os.path.isdir(vpath):
                continue

            debug_print("      " + vpath)

            for (dirname, _, files) in os.walk(vpath):
                for f in files:
                    fpath = dirname + "/" + f
                    rfpath = fpath[len(vpath)+1:]
                    if not os.path.isfile(fpath):
                        continue

                    if "whitelist" in cfg and not rfpath in cfg["whitelist"]:
                        debug_print("      " + fpath + " (" + rfpath + ") - IGNORED")
                        continue

                    debug_print("      " + fpath + " (" + rfpath + ")")

                    ext = os.path.splitext(fpath)[-1]
                    if len(ext) < 2 or ext[1] not in ['c', 'h']:
                        continue

                    furl = None
                    if "file_url_pattern" in cfg:
                        furl = cfg["file_url_pattern"].replace("$version", v).replace("$file", rfpath)

                    add(cat, lib, cfg["url"], furl, v, rfpath, fpath, all_configs)


# ===============================================================
# finalize

jobs = []
for proj in project_list:
    jobs += sorted(project_jobs[proj], key=lambda j: j["name"])

with open(args.file, "w") as f:
    json.dump(jobs, f, indent=4)
