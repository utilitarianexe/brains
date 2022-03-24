# Intro

Neuron simulation software.

# Install

After cloning navigate into the repository and run.

`pip install -e .`

# Run

Runs in two modes

## pygame

Watch network run in real time.
Requires pygame

`python brains/main.py --display pygame --world handwriting`

Current input data for this mode is a small subset of https://www.kaggle.com/sachinpatel21/az-handwritten-alphabets-in-csv-format

I needed
`MESA_LOADER_DRIVER_OVERRIDE=i965`
to make pygame work on Ubuntu

## pyplot

Display potential graphs for each cell using pyplot

`python brains/main.py --display pyplot --world stdp`


## Future

The code is much more flexible than these options suggest.

Much more to come :-)