# Intro

Neuron simulation software.

# Install

After cloning navigate into the repository and run.

`pip install -r requirements.txt`

Note python 3 package.
If installing matplotlib or pygame is an issue it can be run without these depending on mode.

# Run

Runs in two display modes

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

## Options

You can export models to preserve changes to the network during a run using the export option.
You can then import the model using the model_path option. You will also need the environment option
as this is not stored as part of the model. world in a combination of environment and model.


## Future

The code is much more flexible than these options suggest.

Much more to come :-)

## Development

Run tests from root directory with

`pytest`