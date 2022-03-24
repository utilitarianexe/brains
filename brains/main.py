import brains.models.spirit_model as spirit_model
import brains.models.example_model as example_model
import brains.models.simple_model as simple_model
import network
import environment

from collections import namedtuple
import argparse

World = namedtuple('World', 'model environment')

def stdp_world():
    model_parameters = simple_model.stdp_model_parameters()
    network_definition = network.stdp_test_network()
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, environment.STDPTestEnvironment()

def handwriting_world():
    model_parameters = simple_model.handwriting_model_parameters()

    # need like some kind of average starting connection strength thing
    network_definition = network.layer_based_default_network()
    handwriten_environment = environment.HandwritenEnvironment(
        delay=50, frequency=150,
        image_lines=None, shuffle=True,
        last_layer_x_grid_position=network_definition.last_layer_x_grid_position)

    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, handwriten_environment


def create_args():
    my_parser = argparse.ArgumentParser(description='Run brains')
    my_parser.add_argument('--display',
                           type=str,
                           choices=["pygame", "pyplot"],
                           required=True,
                           help='How to display the model.')
    my_parser.add_argument('--world',
                           type=str,
                           choices=["spirit", "stdp", "example", "handwriting"],
                           required=True,
                           help='A world is a combination of a model and an environment. '\
                                'A model is built from ModelParameters and a NetworkDefinition.')
    my_parser.add_argument('--steps',
                           type=int,
                           default=30000,
                           required=False,
                           help='Number of steps to run the model.')

    return my_parser.parse_args()

def create_display(args, model):
    display_type = args.display
    if display_type == "pygame":
        import display.game as game
        display = game.GameDisplay(model)
    elif display_type == "pyplot":
        import display.plot as plot
        display = plot.PlotDisplay(model)
    return display

def create_world(args):
    world_type = args.world
    if world_type == "stdp":
        return stdp_world()
    elif world_type == "spirit":
        return World(spirit_model.default_model(), None)
    elif world_type == "example":
        return World(example_model.ExampleModel(), None)
    elif world_type == "handwriting":
        return handwriting_world()

if __name__ == "__main__" :
    args = create_args()
    brain, environment = create_world(args)
    display = create_display(args, brain)
    steps = args.steps
    for i in range(steps):
        brain.step(i, environment)
        if display is not None:
            display.process_step()
    if display is not None:
        display.final_output()
