# cpp-compile-overhead

Benchmark and accountability tool for C++ compile-time overhead / compile-time health

## Usage

This project consists of three scripts:

* `analyze-file.py` takes a single include and analyzes it (timings, binary size, LoC, ...)
* `generate-jobs.py` defines all the configurations that should be tested
* `execute-jobs.py` takes a list of jobs and calls `analyze-file` for all jobs that were not found in the cache

Finally, there is `generate-data.py` which executes `generate-jobs` followed by `execute-jobs`.

Quickstart:



TODO: link to blog
