# Colored Graph

Python tool to draw graphs in colors.

## Quickstart

Start by saving this description file as as `example.txt`
```
black Robot
    firebrick Battery
        blue Actuator A
        blue Actuator B
        firebrick Power board
            black Computer board
    black Computer board
        darkgreen Sensor A
        darkgreen Sensor B
```
Then run
```bash
pip install .
cgraph example.txt --view
```
A new window should display the graph below

![Example graph](https://raw.githubusercontent.com/SyrianSpock/colored-graph/master/example.png)

Explore the options using `--help`
```bash
cgraph --help
```
And learn more about the description file format below.

## Graph description symbols

Parent/child dependency is encoded by indentation.

There are two kinds of entries in the graph description
- Comments are prefixed by one of the following symbol: `//`, `#`, these lines are ignored
- Nodes are prefixed by the color to display (e.g. red, blue, green, firebrick, darkgreen, etc), invalid colors will throw

## Using the optional header

You can use the first line to specify custom colors as follows
```
[power:firebrick, board:black, actuator:blue, sensor:darkgreen]
_ Robot
    power Battery
        actuator Actuator A
        actuator Actuator B
        power Power board
            black Computer board
    black Computer board
        sensor Sensor A
        sensor Sensor B
```
this will produce the same output as above, but you might find it easier to maintain.

## Dev & Deploy

Deploy by running
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Known issues

- `graphviz` will always save a temporary file when asked to render the graph.
