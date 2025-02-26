# xy-plot-and-save
Python plot & save utility in 2 dimensions (designed for rate-over-time line plots).

With this program, you can select and draw different curves and then save them to disk.

You can also reload the graph from saved files to continue working.

This is useful for designing rate curves that can be processed through administrative interfaces for agents such as [h2agent](https://github.com/testillano/h2agent).

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

