# C++ Compile Health Watchdog

Benchmark and accountability tool for C++ compile-time overhead / compile-time health.

Results are hosted at https://artificial-mind.net/projects/compile-health/.


## Quickstart

```
./generate-data.py some_directory
```

This will create a `compile-health-data.json` in `some_directory` (along with a jobs file, a cache, and project files).

## Contributing

You are welcome to contribute by PR (really awesome persons) or via issues (just normal awesome persons).

Github or Gitlab based projects can be easily added if the headers/sources individually compile without build system.
A simple setup has a `project.json` like this:
```
{
    "type": "github",
    "url": "https://github.com/catchorg/Catch2",
    "working_dir": "include",
    "files": [
        "catch.hpp"
    ],
    "versions": [
        "v2.11.3"
    ]
}
```

Please test your PRs locally by at least running the following command on a Linux (preferably Ubuntu/Debian/Mint) machine:

```
./generate-data.py tmp -p your_new_project
```

(I will run merged PRs on my machine and push the results to https://artificial-mind.net/projects/compile-health/)


## Structure

This project consists of three scripts:

* `analyze-file.py` takes a single include and analyzes it (timings, binary size, LoC, ...)
* `generate-jobs.py` defines all the configurations that should be tested
* `execute-jobs.py` takes a list of jobs and calls `analyze-file` for all jobs that were not found in the cache

Finally, there is `generate-data.py` which executes `generate-jobs` followed by `execute-jobs`.


## Roadmap / TODO

Frontend (https://artificial-mind.net/projects/compile-health/):

* filter by C++ version / build type / compiler
* add custom data client-side (like in speedscope)
* compress data.json and load 3rd party libs lazily
* on mobile, show table fullscreen and have extra text as overlay/hamburger menu, fix the horizontal scrolling of group headers
* a "how to reproduce" option (test file + exact commands)

Backend (this repo):

* add more 3rd party libraries
* support for generate jobs from cmake
* support for Windows
* test different standard libraries (`libc++` vs `libstdc++`)
* get size of debug symbols

## Required Dependencies

For building all configured projects.

### Ubuntu / Debian

```
sudo apt install \
libsuitesparse-dev \
libmetis-dev \
libcholmod3
```

(I probably missed a few)
