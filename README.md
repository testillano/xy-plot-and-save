# xy-plot-and-save

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3-3776ab.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://github.com/testillano)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/testillano/xy-plot-and-save/graphs/commit-activity)

Python plot & save utility in 2 dimensions (designed for value-over-time line plots).

With this program, you can select and draw different curves and then save them to disk.

You can also reload the graph from saved files to continue working.

The `Save` button writes two files (basename given by `--output`, `example` by default):

* `<basename>.json`: the session (duration, timeline ticks, values range, y-axis label and the values of every curve). Load it with `--input <basename>` to continue working: its parameters are used, so there is no need to repeat them.
* `<basename>.txt`: a plain text table with the painted times and the value of every curve (`-` where a curve has no point).

Click to paint the point nearest to the pointer, or drag to paint a curve (fast drags are interpolated). Values are rounded to `--value-module`, and those below `--min-value` are zeroed.

This is useful for designing traffic load profiles (`y-value = rate (cps)`) that can be processed through administrative interfaces for agents such as [h2agent](https://github.com/testillano/h2agent).

# Requirements

```bash
$ pip3 install -r requirements.txt
```

# Usage

```bash
$ python3 plot.py --help
```

# Using docker image

## Build

```bash
$ docker build -t plot-app .
```

## Run

```bash
$ xhost +local:docker
$ docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v ${PWD}:/home plot-app --labels test1,test2
```

