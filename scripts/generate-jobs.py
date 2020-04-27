#!/usr/bin/env python3

import re
import glob
import os
import argparse
import subprocess
import platform
import shutil
import distutils.dir_util
import json

parser = argparse.ArgumentParser(
    description="Generate a tasks for C++ compile-health analyzer")
parser.add_argument("file", metavar="F",
                    help="file to store the schedule in (e.g. jobs.json)")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-p", "--project", help="only generate a specific project")
parser.add_argument("-c", "--configs", type=int,
                    help="only generate a limited number of configs")
parser.add_argument("-d", "--dir", required=True,
                    help="tmp dir where downloaded sources are stored")

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

            variants = [
                ["Debug", ['-O0', '-g']],
                ["RelWithDebInfo", ['-O2', '-g', '-DNDEBUG']],
                ["Release", ['-O3', '-DNDEBUG']],
            ]

            for libcpp in [False, True]:
                if libcpp and not cc[0].startswith("Clang"):
                    continue

                if libcpp:
                    continue  # TODO: install multiple versions

                extra_args = []
                var_suffix = ""
                if libcpp:
                    extra_args.append('-stdlib=libc++')
                    var_suffix = " (libc++)"

                for cpp in [11, 14, 17]:
                    for variant in variants:
                        c = Config()
                        c.cpp = cpp
                        c.args = variant[1] + extra_args + ["-march=skylake"]
                        c.variant = variant[0] + var_suffix
                        c.compiler = cc[1]
                        c.compiler_name = cc[0]
                        yield c

    else:
        assert False, "unknown platform"


all_configs = list(generate_configs())

since_cpp14_configs = [c for c in all_configs if c.cpp >= 14]
since_cpp17_configs = [c for c in all_configs if c.cpp >= 17]


def truncate_cfgs(cfgs):
    if args.configs and args.configs < len(cfgs):
        cfgs = cfgs[0:args.configs]
    return cfgs


all_configs = truncate_cfgs(all_configs)
since_cpp14_configs = truncate_cfgs(since_cpp14_configs)
since_cpp17_configs = truncate_cfgs(since_cpp17_configs)

project_list = []
project_jobs = {}


def add(category, project, project_url, url, version, name, file, configs, cwd, *, extra_args=[], include_dirs=[]):
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
            "args": c.make_args() + extra_args,
            "cpp": c.cpp,
            "include_dirs": include_dirs,
            "compiler": c.compiler,
            "compiler_name": c.compiler_name,
            "working_dir": cwd
        }
        project_jobs[project].append(job)
        if args.verbose:
            print("added {}".format(job))

# ===============================================================
# Projects
# ===============================================================


if not args.project:

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
        add("Standard Library", "C++ Standard Library", url_cpp,
            url_cpp + "/" + h, "", "<" + h + ">", h, all_configs, args.dir)

    for h in [
        "shared_mutex",
    ]:
        add("Standard Library", "C++ Standard Library", url_cpp,
            url_cpp + "/" + h, "", "<" + h + ">", h, since_cpp14_configs, args.dir)

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
            if c.compiler.endswith("/g++-7") and h == "filesystem":
                continue
            if (c.compiler.endswith("/g++-7") or c.compiler.endswith("/g++-8")) and h in ["memory_resource", "charconv", "execution"]:
                continue

            add("Standard Library", "C++ Standard Library", url_cpp,
                url_cpp + "/" + h, "", "<" + h + ">", h, [c], args.dir)

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
        add("Standard Library", "C Standard Library",
            url_c, None, "", "<" + h + ">", h, all_configs, args.dir)

    # ===============================================================
    # c POSIX

    for h in [
        "aio.h",
        "arpa/inet.h",
        "assert.h",
        "complex.h",
        "cpio.h",
        "ctype.h",
        "dirent.h",
        "dlfcn.h",
        "errno.h",
        "fcntl.h",
        "fenv.h",
        "float.h",
        "fmtmsg.h",
        "fnmatch.h",
        "ftw.h",
        "glob.h",
        "grp.h",
        "iconv.h",
        "inttypes.h",
        "iso646.h",
        "langinfo.h",
        "libgen.h",
        "limits.h",
        "locale.h",
        "math.h",
        "monetary.h",
        "mqueue.h",
        # "ndbm.h", missing on ubuntu
        "net/if.h",
        "netdb.h",
        "netinet/in.h",
        "netinet/tcp.h",
        "nl_types.h",
        "poll.h",
        "pthread.h",
        "pwd.h",
        "regex.h",
        "sched.h",
        "search.h",
        "semaphore.h",
        "setjmp.h",
        "signal.h",
        "spawn.h",
        "stdarg.h",
        "stdbool.h",
        "stddef.h",
        "stdint.h",
        "stdio.h",
        "stdlib.h",
        "string.h",
        "strings.h",
        "stropts.h",
        "sys/ipc.h",
        "sys/mman.h",
        "sys/msg.h",
        "sys/resource.h",
        "sys/select.h",
        "sys/sem.h",
        "sys/shm.h",
        "sys/socket.h",
        "sys/stat.h",
        "sys/statvfs.h",
        "sys/time.h",
        "sys/times.h",
        "sys/types.h",
        "sys/uio.h",
        "sys/un.h",
        "sys/utsname.h",
        "sys/wait.h",
        "syslog.h",
        "tar.h",
        "termios.h",
        "tgmath.h",
        "time.h",
        "unistd.h",
        "utime.h",
        "utmpx.h",
        "wchar.h",
        "wctype.h",
        "wordexp.h",
    ]:
        add("Standard Library", "C POSIX Library",
            "https://en.wikipedia.org/wiki/C_POSIX_library", None, "", "<" + h + ">", h, all_configs, args.dir)


# ===============================================================
# stdlibs

# TODO: properly get source for different stdlibs
# debug_print("getting standard libraries")
#
# def get_stdlib(url, versions, name):
#     global args
#     repo_dir = os.path.join(args.dir, "stdlibs", name)
#     if not os.path.exists(repo_dir):
#         git_args = ["git", "clone", url, repo_dir]
#         debug_print(" .. getting stdlib via " + repo_dir)
#         subprocess.check_call(git_args)
#
# get_stdlib("git://gcc.gnu.org/git/gcc.git", [], "libcstd++")


# ===============================================================
# libs

debug_print("parsing libraries")


def add_project_files(cfg, cat, lib, libpath):
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
                    debug_print("      " + fpath +
                                " (" + rfpath + ") - IGNORED")
                    continue

                debug_print("      " + fpath + " (" + rfpath + ")")

                ext = os.path.splitext(fpath)[-1]
                if len(ext) < 2 or ext[1] not in ['c', 'h']:
                    continue

                furl = None
                if "file_url_pattern" in cfg:
                    furl = cfg["file_url_pattern"].replace(
                        "$version", v).replace("$file", rfpath)
                if "no_url_for_files" in cfg:
                    if re.fullmatch(cfg["no_url_for_files"], f):
                        furl = None

                add(cat, lib, cfg["url"], furl, v,
                    rfpath, rfpath, all_configs, vpath, include_dirs=[vpath])


def make_github_file_url(cfg, v, f):
    return os.path.join(cfg["url"], "blob", v, cfg["working_dir"], f)


def make_gitlab_file_url(cfg, v, f):
    return os.path.join(cfg["url"], "-", "blob", v, cfg["working_dir"], f)


fetched_repos = set()


def get_repo_files(url, version, base_dir, target_dir):
    global args
    global fetched_repos

    debug_print("      .. getting files from " + url)

    urltype = None
    # e.g. https://github.com/boostorg/config
    if url.startswith("https://github.com"):
        urltype = "github"
        m = re.fullmatch(r"https://github\.com/([\w-]+)/([\w-]+)/?", url)
        assert m is not None, "malformed url"
        user = m.group(1)
        proj = m.group(2)

    # e.g. https://gitlab.com/libeigen/eigen
    elif url.startswith("https://gitlab.com"):
        urltype = "gitlab"
        m = re.fullmatch(r"https://gitlab\.com/([\w-]+)/([\w-]+)", url)
        assert m is not None, "malformed url"
        user = m.group(1)
        proj = m.group(2)

    # e.g. https://graphics.rwth-aachen.de:9000/OpenMesh/OpenMesh
    elif url.startswith("https://graphics.rwth-aachen.de:9000"):
        urltype = "rwth-graphics"
        m = re.fullmatch(
            r"https://graphics\.rwth-aachen\.de:9000/([\w-]+)/([\w-]+)", url)
        assert m is not None, "malformed url"
        user = m.group(1)
        proj = m.group(2)

    else:
        assert False, "unknown/unsupported repo"

    repo_dir = os.path.join(args.dir, "repos", urltype, user, proj)
    debug_print("      .. repo in " + repo_dir)
    if not os.path.exists(repo_dir):
        git_args = ["git", "clone", url, repo_dir]
        debug_print("      .. running {}".format(git_args))
        subprocess.check_call(git_args)

    if not url in fetched_repos:  # only fetch once
        debug_print("      .. git fetch")
        subprocess.check_call(["git", "fetch"], cwd=repo_dir)
        fetched_repos.add(url)

    debug_print("      .. getting version " + version)
    subprocess.check_call(["git", "checkout", version], cwd=repo_dir)

    src_dir = os.path.join(repo_dir, base_dir)
    debug_print("      .. copy {} to {}".format(src_dir, target_dir))

    distutils.dir_util.copy_tree(src_dir, target_dir)


def add_project_git(cfg, cat, lib, libpath, make_file_url):
    assert "url" in cfg, "project.json needs at least an URL"
    global args

    if "enabled" in cfg and not cfg["enabled"]:
        return

    lib_tmp_dir = os.path.join(args.dir, libpath)

    files = []
    for f in cfg["files"]:
        assert "*" not in f, "globbing not supported"
        files.append(f)

    missing_versions = []
    for v in cfg["versions"]:
        any_missing = False
        for f in files:
            file_path = os.path.join(lib_tmp_dir, "versions", v, "src", f)
            if not os.path.exists(file_path):
                any_missing = True
                break
        if any_missing:
            missing_versions.append(v)

    for v in missing_versions:
        debug_print("      .. getting version " + v)

        version_dir = os.path.join(lib_tmp_dir, "versions", v, "src")
        get_repo_files(cfg["url"], v, cfg["working_dir"], version_dir)

        # get dependencies
        if "dependencies" in cfg:
            for dep_url in cfg["dependencies"]:
                dep_cfg = cfg["dependencies"][dep_url]
                assert "version" in dep_cfg
                assert "dir" in dep_cfg

                dep_version = dep_cfg["version"]
                if dep_version == "*":
                    dep_version = v

                dep_dir = os.path.join(lib_tmp_dir, "versions", v, "deps")
                get_repo_files(dep_url, dep_version, dep_cfg["dir"], dep_dir)

    extra_args = []
    if "args" in cfg:
        extra_args = cfg["args"]

    cfgs = all_configs
    if "min-cpp" in cfg:
        if cfg["min-cpp"] == 11:
            cfgs = all_configs
        elif cfg["min-cpp"] == 14:
            cfgs = since_cpp14_configs
        elif cfg["min-cpp"] == 17:
            cfgs = since_cpp17_configs
        else:
            assert False, "unknown cpp min version"

    for v in cfg["versions"]:
        for f in files:
            file_path = os.path.join(lib_tmp_dir, "versions", v, "src", f)
            if not os.path.exists(file_path):
                print("missing file " + file_path)
                assert False, "missing file"
            furl = make_file_url(cfg, v, f)

            vname = v
            for s in [  # TODO configurable
                "release-",
                "release/",
                "boost-",
            ]:
                if vname.startswith(s):
                    vname = vname[len(s):]

            if "version-prefix" in cfg and vname.startswith(cfg["version-prefix"]):
                vname = vname[len(cfg["version-prefix"]):]

            src_dir = os.path.join(lib_tmp_dir, "versions", v, "src")
            dep_dir = os.path.join(lib_tmp_dir, "versions", v, "deps")

            add(cat, lib, cfg["url"], furl, vname, f, f, cfgs, os.path.join(
                lib_tmp_dir, "versions", v), extra_args=extra_args, include_dirs=[src_dir, dep_dir])


for cat in sorted(os.listdir("libs")):
    catpath = "libs/" + cat
    if not os.path.isdir(catpath):
        continue

    debug_print("  " + catpath)

    for lib in sorted(os.listdir(catpath)):
        libpath = catpath + "/" + lib
        if not os.path.isdir(libpath):
            continue

        debug_print("    " + libpath)

        if args.project and args.project != lib:
            debug_print("       .. skipped")
            continue

        cfgpath = libpath + "/project.json"
        assert os.path.exists(cfgpath), "no config found in " + cfgpath
        with open(cfgpath, "r") as f:
            cfg = json.load(f)
        assert "type" in cfg, "no type specified in project.json"

        if cfg["type"] == "file":
            add_project_files(cfg, cat, lib, libpath)

        elif cfg["type"] == "github":
            add_project_git(cfg, cat, lib, libpath, make_github_file_url)

        elif cfg["type"] == "gitlab":
            add_project_git(cfg, cat, lib, libpath, make_gitlab_file_url)

        else:
            assert False, "unknown project type " + cfg["type"]


# ===============================================================
# finalize

jobs = []
for proj in project_list:
    jobs += sorted(project_jobs[proj], key=lambda j: j["name"])

with open(args.file, "w") as f:
    json.dump(jobs, f, indent=4)
