# cpp-compile-overhead

Benchmark and accountability tool for C++ compile-time overhead / compile-time health.

Results are hosted at https://artificial-mind.net/projects/compile-health/.


## Quickstart

```
generate-data.py some_directory
```

This will create a `compile-health-data.json` in `some_directory` (along with a jobs file and a cache).


## Structure

This project consists of three scripts:

* `analyze-file.py` takes a single include and analyzes it (timings, binary size, LoC, ...)
* `generate-jobs.py` defines all the configurations that should be tested
* `execute-jobs.py` takes a list of jobs and calls `analyze-file` for all jobs that were not found in the cache

Finally, there is `generate-data.py` which executes `generate-jobs` followed by `execute-jobs`.
