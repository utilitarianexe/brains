# Intro

Neuron simulation software.

# Instructions

Runs in two modes

## pygame

Watch network run in real time.
Requires pygame

`python main.py pygame`

Current input data for this mode is a small subset of https://www.kaggle.com/sachinpatel21/az-handwritten-alphabets-in-csv-format

I needed
`MESA_LOADER_DRIVER_OVERRIDE=i965`
to make pygame work on Ubuntu

## pyplot

Display potential graphs for each cell using pyplot

`python main.py pyplot`


## Future

The code is much more flexible than these options suggest.
To create your own networks and parameter spaces see default_runs.py

Much more to come :-)