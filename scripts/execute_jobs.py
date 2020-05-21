#!/usr/bin/env python3

import shutil
import gzip
import os
import argparse
import subprocess
import platform
import json

import scripts.analyze_file

def run(jobs_file, dest_file, dest_dir, cache_file, verbose):
    
    is_windows = any(platform.win32_ver())
    is_linux = not is_windows

    job_cache = {}


    def build_result_data(results):
        proj_list = []
        variant_to_idx = {}
        variants = []
        cresult = {
            "projects": proj_list,
            "variants": variants
        }
        curr_proj = {"name": None, "version": None}
        curr_files = None
        curr_file = {"name": None}
        curr_results = None
        for j in results:
            varid = j["compiler"] + " " + j["argstr"]
            if varid not in variant_to_idx:
                variant_to_idx[varid] = len(variants)
                variants.append({
                    "name": j["variant"],
                    "compiler_name": j["compiler_name"],
                    "compiler_path": j["compiler"],
                    "compiler_version": j["compiler_version"],
                    "cpp": j["cpp"],
                    "args": j["argstr"],
                })

            if curr_proj["name"] != j["project"] or curr_proj["version"] != j["version"]:
                curr_files = []
                curr_file = {"name": None}
                curr_proj = {
                    "name": j["project"],
                    "version": j["version"],
                    "url": j["project_url"],
                    "category": j["category"],
                    "files": curr_files,
                }
                proj_list.append(curr_proj)

            if curr_file["name"] != j["name"]:
                curr_results = []
                curr_file = {
                    "name": j["name"],
                    "url": j["url"],
                    "results": curr_results
                }
                curr_files.append(curr_file)

            curr_results.append([
                variant_to_idx[varid],
                int(1000 * j["compile_time"]),
                int(1000 * j["compile_time_base"]),
                int(1000 * j["preprocessing_time"]),
                int(1000 * j["preprocessing_time_base"]),
                j["line_count"],
                j["line_count_raw"],
                j["object_size"],
                j["object_size_base"],
                j["text_size"],
                j["data_size"],
                j["bss_size"],
                j["string_size"],
                j["code_symbol_size"],
                j["data_symbol_size"],
                j["weak_symbol_size"],
                j["symbol_name_size"],
                j["string_count"],
                j["undefined_symbol_count"],
                j["code_symbol_count"],
                j["data_symbol_count"],
                j["weak_symbol_count"],
            ])

        # TODO: proper gzipped result
        # with gzip.GzipFile(dest_file + ".gz", "w") as f:
        #     f.write(json.dumps(results).encode("utf-8"))

        return cresult


    # ===============================================
    # read jobs and cache


    with open(jobs_file, "r") as f:
        jobs = json.load(f)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            job_cache = json.load(f)

    print("executing {} jobs".format(len(jobs)))
    print("found {} cached jobs in total".format(len(job_cache)))

    found_cached = 0

    idx = 0

    results = []
    to_execute = []

    for j in jobs:
        id = []
        if j["version"] != "":
            id.append(j["version"])
        id.append(j["file"])
        id.append(j["compiler"])
        id += j["args"]
        id = ":".join(id)
        j["id"] = idx
        j["cache-key"] = id
        j["argstr"] = " ".join(j["args"])

        res = {}

        if id in job_cache:
            res = job_cache[id]
            found_cached += 1
            for k in res:
                j[k] = res[k]
            results.append(j)
        else:
            to_execute.append(j)

        idx += 1

    # write before
    with open(dest_file, "w") as f:
        json.dump(build_result_data(results), f)

    print("was able to reuse {} results from cache".format(found_cached))
    print("has to execute {} more jobs".format(len(to_execute)))

    done = 0
    for j in to_execute:
        id = j["cache-key"]
        compiler_args = j["args"]
        for d in j["include_dirs"]:
            if is_windows:
                compiler_args += ["/I" + d]
            else:
                compiler_args += ["-I" + d]
        if verbose:
            print("[{}/{}] executing '{} {}'".format(done, len(to_execute), j['compiler'], " ".join(compiler_args)))
        res = scripts.analyze_file.run(j['file'], dest_dir, j['compiler'], compiler_args, verbose)

        res = json.loads(res)
        job_cache[id] = res

        # write cache
        if os.path.exists(cache_file):
            shutil.copy(cache_file, cache_file + ".prev")
        with open(cache_file, "w") as f:
            json.dump(job_cache, f, indent=4)

        for k in res:
            j[k] = res[k]

        results.append(j)
        done += 1


    # write after
    with open(dest_file, "w") as f:
        json.dump(build_result_data(results), f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Execute jobs for C++ compile-health analyzer")
    parser.add_argument("file", metavar="J", help="jobs file (e.g. jobs.json)")
    parser.add_argument("result", metavar="R", help="result file (e.g. data.json)")
    parser.add_argument("-c", "--cache", required=True, help="cache file")
    parser.add_argument("-d", "--dir", required=True, type=str,
                        help="temporary directory to use (e.g. /tmp)")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    run(args.file, args.result, args.dir, args.cache, args.verbose)