# Intro

Neural network simulation software.

Biased towards being more like a squishy brain and less like a traditional AI.

## General concept

Running the program runs a "world". A world consists of a brain/model and an environment.

A brain consists of a network, a set of parameters, and choice of a model of a neuron to simulate.

An environment provides inputs to the brain and receives outputs.

# Install

After cloning navigate into the repository and run.

`pip install -r requirements.txt`

Note this is a python 3 app.
If installing matplotlib or pygame is an issue it can be run without these depending on mode.

# Run

Runs in two display modes or with no display

## Basic learning using STDP

`python brains/main.py --epochs=5000  --world=easy --export_name=easy_network`

Runs a simple brain for 2000000 steps(400 per epoch). Input from three neurons. One that fires randomly and a pair where at least one fires but which one is random. There are two output cells. If the same output cell fires as the input cell in the same row the network is rewarded and a win is recorded. The network starts out unbiased but will learn to fire the right output for the input.

## pygame

Watch network run in real time by importing the brain you just trained.

`python brains/main.py --environment=easy --import_name=easy_network --display=pygame`

Or watch a more complex network and environment(training for this one still does not work).

`python brains/main.py --display pygame --world handwriting`

Current input data for this mode is a small subset of https://www.kaggle.com/sachinpatel21/az-handwritten-alphabets-in-csv-format

Clicking on the screen will disable the display speeding up the program. Clicking again will re-enable the display.

I needed
`MESA_LOADER_DRIVER_OVERRIDE=i965`
to make pygame work on Ubuntu

## pyplot

Display potential graphs for each cell using pyplot

`python brains/main.py --display pyplot --world stdp --epochs 5`

## Options

You can export models to preserve changes to the network during a run using the export_name option.
You can then import the model using the import_name option. You will also need the environment option
as this is not stored as part of the model. world is a combination of environment and model.


## Future

The code is much more flexible than these options suggest.

Much more to come :-)

## Development

Run tests from root directory with

`pytest`