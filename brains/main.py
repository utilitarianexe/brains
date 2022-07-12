import brains.models.spirit_model as spirit_model
import brains.models.example_model as example_model
import brains.models.simple_model as simple_model
import brains.models.simple_model_builder as simple_model_builder
import brains.network_definitions as network_definitions
import brains.utils as utils

from brains.environment.easy import EasyEnvironment
from brains.environment.handwriting import HandwritingEnvironment
from brains.environment.mnist import MnistEnvironment
from brains.environment.stdp import STDPTestEnvironment
from brains.environment.parameter import ParameterTestEnvironment

from pathlib import Path
from collections import namedtuple
import argparse
import json
import signal
import sys

World = namedtuple('World', 'model environment')

def parameter_test_world():
    model_parameters = simple_model_builder.ModelParameters(starting_dopamine=0.0)
    network_definition = network_definitions.parameter_test_network()
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, ParameterTestEnvironment()

def stdp_world(parameters):
    model_parameters = simple_model_builder.ModelParameters(epoch_length=parameters.epoch_length)
    model_parameters.synapse_type_parameters.max_strength = 0.4
    network_definition = network_definitions.stdp_test_network()
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, STDPTestEnvironment()

def handwriting_world(parameters):
    model_parameters = simple_model_builder.handwriting_model_parameters(
        epoch_length=parameters.epoch_length,
        epoch_delay=parameters.epoch_delay)
    network_definition = network_definitions.layer_based_default_network()
    environment = HandwritingEnvironment(
        parameters.epoch_length, parameters.input_delay, {'o': 0, 'x': 1},
        image_lines=None, shuffle=True,
        file_name=parameters.handwritten_file_name)

    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, environment

def mnist_world(parameters):
    model_parameters = simple_model_builder.handwriting_model_parameters(
        epoch_length=parameters.epoch_length,
        epoch_delay=parameters.epoch_delay)
    network_definition = network_definitions.mnist_network(
        number_of_outputs=parameters.mnist_number_of_outputs)
    environment = MnistEnvironment(parameters.epoch_length, parameters.input_delay,
                                   number_of_possible_outputs=parameters.mnist_number_of_outputs)
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, environment


def easy_world(parameters):
    model_parameters = simple_model_builder.handwriting_model_parameters(
        epoch_length=parameters.epoch_length,
        epoch_delay=parameters.epoch_delay)
    model_parameters.synapse_type_parameters.max_strength = 0.4

    # need like some kind of average starting connection strength thing
    network_definition = network_definitions.easy_layer_network()
    easy_environment = EasyEnvironment(parameters.epoch_length, parameters.input_delay)
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, easy_environment

def user_specified_world(parameters):
    file_path = utils.data_dir_file_path(parameters.import_name)
    model_file = open(file_path)
    blob = json.load(model_file)
    model = simple_model_builder.import_model(blob)
    if parameters.environment_type == 'handwriting':
        model_environment = HandwritingEnvironment(
            model.epoch_length, parameters.input_delay, {'o': 0, 'x': 1},
            image_lines=None, shuffle=True,
            file_name=parameters.handwritten_file_name)
    elif parameters.environment_type == 'mnist':
        model_environment = MnistEnvironment(
            model.epoch_length, parameters.input_delay,
            number_of_possible_outputs=parameters.mnist_number_of_outputs)
    elif parameters.environment_type == 'easy':
        model_environment = EasyEnvironment(model.epoch_length, parameters.input_delay)
    elif parameters.environment_type == 'stdp':
        model_environment = STDPTestEnvironment(model.epoch_length)
    elif parameters.environment_type == 'parameter':
        model_environment = STDPTestEnvironment(model.epoch_length)
    return model, model_environment

def create_world(parameters):
    
    if parameters.world_type and parameters.environment_type:
        raise Exception("User should either create world with(import_name and environment) or " \
                        "provide world_type")

    if parameters.import_name and parameters.environment_type:
        return user_specified_world(parameters)
    elif parameters.import_name and parameters.world_type:
        parameters.environment_type = parameters.world_type
        return user_specified_world(parameters)
    
    if parameters.world_type:
        if parameters.world_type == "parameter":
            return parameter_test_world()
        elif parameters.world_type == "stdp":
            return stdp_world(parameters)
        elif parameters.world_type == "easy":
            return easy_world(parameters)
        elif parameters.world_type == "spirit":
            return World(spirit_model.default_model(), None)
        elif parameters.world_type == "example":
            return World(example_model.ExampleModel(), None)
        elif parameters.world_type == "handwriting":
            return handwriting_world(parameters)
        elif parameters.world_type == "mnist":
            return mnist_world(parameters)

    print("Not enough information provided. Either supply a world argument or both " \
          "a import_name and an environment to run it in")
    sys.exit(0)

def create_display(display_type, model, environment=None):
    if display_type == "pygame":
        import display.game as game
        display = game.GameDisplay(model, environment=environment)
    elif display_type == "pyplot":
        import display.plot as plot
        display = plot.PlotDisplay(model)
    else:
        display = None
    return display


def export(brain, export_name):
    blob = brain.export()
    base_path = Path(__file__).parent / "data"
    file_path = (base_path / export_name).resolve()
    output_file = open(file_path, 'w')
    json.dump(blob, output_file, sort_keys=True, indent=4)

def create_args():
    my_parser = argparse.ArgumentParser(description='Run brains')
    my_parser.add_argument('--display_type', '--display',
                           type=str,
                           choices=["pygame", "pyplot", ""],
                           required=True,
                           help='How to display the model.')
    my_parser.add_argument(
        '--world_type', '--world',
        type=str,
        choices=["spirit", "stdp", "example", "handwriting", "easy", "mnist", "parameter"],
        required=False,
        help='A world is a combination of a model and an environment. '\
        'A model is built from ModelParameters and a NetworkDefinition.')
    my_parser.add_argument('--epochs',
                           type=int,
                           default=10000,
                           required=False,
                           help='Number of epochs to run the model.')
    my_parser.add_argument('--epoch_length',
                           type=int,
                           default=400,
                           required=False,
                           help='Number of steps per epoch.')
    my_parser.add_argument('--input_delay',
                           type=int,
                           default=50,
                           required=False,
                           help='Number of steps per epoch.')
    my_parser.add_argument('--epoch_delay',
                           type=int,
                           default=50,
                           required=False,
                           help='Number of steps per epoch.')
    my_parser.add_argument('--export_name',
                           type=str,
                           required=False,
                           help='Export model to at the end of a run. Just provide a name it will be added to the data directory.')
    
    # Create your own world by combining an imported model(network + parameters) and a selected
    # environment. For convenience, if world is supplied but not environment, the environment for that
    # world will be used with the imported model.
    my_parser.add_argument('--import_name',
                           type=str,
                           required=False,
                           help='Import model. Should be the name of a file in the data directory.')
    my_parser.add_argument('--environment_type', '--environment',
                           choices=["stdp", "handwriting", "easy", "mnist", "parameter"],
                           type=str,
                           required=False,
                           help='Type of environment to run.')
    my_parser.add_argument('--handwritten_file_name',
                           default="o_x_hand_written_short.csv",
                           type=str,
                           required=False,
                           help='Images to use for handwriting environment.')
    my_parser.add_argument('--profile',
                           default=False,
                           type=bool,
                           required=False,
                           help='Profile code all other options are ignored if selected.')
    my_parser.add_argument('--mnist_number_of_outputs',
                           default=10,
                           type=int,
                           required=False,
                           help='Number of outputs of mnist network.')
    my_parser.add_argument('--attempt_warp',
                           default=False,
                           type=bool,
                           required=False,
                           help="Warp to speed up code when possible may contain errors " \
                           "with unsupervised learning")
    return my_parser.parse_args()


def main(parameters):
    brain, environment = create_world(parameters)
    
    def exit_handler(signum, frame):
        if parameters.export_name:
            export(brain, parameters.export_name)
        sys.exit(0)
    signal.signal(signal.SIGINT, exit_handler)

    # display really should not take brain and environment as parameters either
    display = create_display(parameters.display_type, brain, environment=environment)
    display_active = display is not None
    brain_output_ids = []
    should_exit = False
    for i in range(parameters.steps):
        environment.step(i, brain_output_ids)
        warp_allowed = parameters.attempt_warp and not display_active
        brain_output_ids = brain.step(i,
                                      environment.stimuli(i),
                                      environment.has_reward(), environment.active(i))

        if (i - parameters.input_delay) % parameters.epoch_length == 0:
            for text in brain.text_output():
                print(text)

        if display is not None:
            epoch = (i - parameters.input_delay) // parameters.epoch_length
            should_exit = display.process_step(i, epoch=epoch)
            if display._get_mode() == "none":
                display_active = False
            
            if should_exit:
                if parameters.export_name:
                    export(brain, parameters.export_name)
                sys.exit(0)

    if display is not None:
        display.final_output()

    if parameters.export_name:
        export(brain, parameters.export_name)
  

if __name__ == "__main__" :
    parameters = create_args()
    parameters.steps = parameters.epoch_length * parameters.epochs

    if not parameters.profile:
        main(parameters)
        sys.exit(0)
    
    import cProfile, pstats, io
    from pstats import SortKey
    pr = cProfile.Profile()
    pr.enable()
    main(parameters)

    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

