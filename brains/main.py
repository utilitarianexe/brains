import brains.models.spirit_model as spirit_model
import brains.models.example_model as example_model
import brains.models.simple_model as simple_model
import network
import environment

from pathlib import Path
from collections import namedtuple
import argparse
import json
import signal

World = namedtuple('World', 'model environment')

def stdp_world(input_balance, epoch_length):
    model_parameters = simple_model.stdp_model_parameters(input_balance, warp=warp)
    network_definition = network.stdp_test_network()
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, environment.STDPTestEnvironment(epoch_length)

def handwriting_world(file_name, epoch_length, input_delay=50, warp=True):
    model_parameters = simple_model.handwriting_model_parameters(True,
                                                                 noise_factor=0.5,
                                                                 warp=warp)

    # need like some kind of average starting connection strength thing
    network_definition = network.layer_based_default_network()
    handwriten_environment = environment.HandwritenEnvironment(
        input_delay=input_delay, epoch_length=epoch_length,
        image_lines=None, shuffle=True,
        last_layer_x_grid_position=network_definition.last_layer_x_grid_position,
        file_name=file_name)

    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, handwriten_environment

def easy_world(epoch_length, input_delay=50, warp=True):
    model_parameters = simple_model.handwriting_model_parameters(True,
                                                                 noise_factor=0.5,
                                                                 warp=warp)

    # need like some kind of average starting connection strength thing
    network_definition = network.easy_layer_network()
    easy_environment = environment.EasyEnvironment(epoch_length, input_delay)
    model = simple_model.SimpleModel(network_definition, model_parameters)
    return model, easy_environment


def user_specified_world(import_name, environment_type, handwritten_file_name,
                         epoch_length, input_delay=50, warp=True):
    print(handwritten_file_name)


    base_path = Path(__file__).parent / "data"
    file_path = (base_path / import_name).resolve()
    model_file = open(file_path)
    blob = json.load(model_file)
    model = simple_model.import_model(blob, warp=warp)
    if environment_type == 'handwriting':
        model_environment = environment.HandwritenEnvironment(
            input_delay=input_delay, epoch_length=epoch_length,
            image_lines=None, shuffle=True,
            last_layer_x_grid_position=model.network_definition.last_layer_x_grid_position,
            file_name=handwritten_file_name)
    elif environment_type == 'easy':
        model_environment = environment.EasyEnvironment(epoch_length, input_delay)
    elif environment_type == 'stdp':
        model_environment = environment.STDPTestEnvironment()
    return model, model_environment

def create_args():
    my_parser = argparse.ArgumentParser(description='Run brains')
    my_parser.add_argument('--display',
                           type=str,
                           choices=["pygame", "pyplot"],
                           required=False,
                           help='How to display the model.')
    my_parser.add_argument(
        '--world',
        type=str,
        choices=["spirit", "stdp", "example", "handwriting", "input_balance", "easy"],
        required=False,
        help='A world is a combination of a model and an environment. '\
        'A model is built from ModelParameters and a NetworkDefinition.')
    my_parser.add_argument('--steps',
                           type=int,
                           default=30000,
                           required=False,
                           help='Number of steps to run the model.')
    my_parser.add_argument('--epoch_length',
                           type=int,
                           default=400,
                           required=False,
                           help='Number of steps between presentations of input to a brain.')
    my_parser.add_argument('--export_name',
                           type=str,
                           required=False,
                           help='Export model to at the end of a run. Just provide a name it will be added to the data directory.')
    
    # create your own world with an imported model(network + parameters) and a selected environment.
    my_parser.add_argument('--import_name',
                           type=str,
                           required=False,
                           help='Import model. Should be the name of a file in the data directory.')
    my_parser.add_argument('--environment',
                           choices=["stdp", "handwriting", "easy"],
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
    return my_parser.parse_args()

def create_display(display_type, model):
    if display_type == "pygame":
        import display.game as game
        display = game.GameDisplay(model)
    elif display_type == "pyplot":
        import display.plot as plot
        display = plot.PlotDisplay(model)
    else:
        display = None
    return display

def create_world(world_type, epoch_length, import_name,
                 environment_type, handwritten_file_name):
    if world_type and import_name:
        raise Exception("User should either create world with(import_name and environment) or " \
                        "provide\ world_type")
    
    if world_type:
        if world_type == "stdp":
            return stdp_world(False, epoch_length)
        elif world_type == "easy":
            return easy_world(epoch_length)
        elif world_type == "spirit":
            return World(spirit_model.default_model(), None)
        elif world_type == "example":
            return World(example_model.ExampleModel(), None)
        elif world_type == "handwriting":
            return handwriting_world(handwritten_file_name, epoch_length)
        elif world_type == "input_balance":
            return stdp_world(True, epoch_length)

    if import_name and environment_type:
        return user_specified_world(import_name, environment_type, handwritten_file_name, epoch_length, warp=False)

    print("Not enough information provided. Either supply a world argument or both a import_name and an environment to run it in")
    quit()

def export(brain, export_name):
    blob = brain.export()
    base_path = Path(__file__).parent / "data"
    file_path = (base_path / export_name).resolve()
    output_file = open(file_path, 'w')
    json.dump(blob, output_file, sort_keys=True, indent=4)

def main(steps, epoch_length,
         world_type="", import_name="",
         environment_type="", handwritten_file_name="",
         display_type="", export_name=""):

    brain, environment = create_world(world_type, epoch_length,
                                      import_name, environment_type,
                                      handwritten_file_name)
    def handler(signum, frame):
        if export_name:
            export(brain, export_name)
        exit(1)

    signal.signal(signal.SIGINT, handler)

    display = create_display(display_type, brain)
    for i in range(steps):
        environment.step(i)
        brain.step(i, environment)
        if display is not None:
            display.process_step()
    if display is not None:
        display.final_output()

    if export_name:
        export(brain, export_name)
  

if __name__ == "__main__" :
    args = create_args()
    steps = args.steps
    world_type = args.world
    import_name = args.import_name
    environment_type = args.environment
    handwritten_file_name = args.handwritten_file_name
    display_type = args.display
    export_name = args.export_name
    profile = args.profile
    epoch_length = args.epoch_length

    if profile:
        import cProfile, pstats, io
        from pstats import SortKey
        pr = cProfile.Profile()
        pr.enable()
        main(steps, epoch_length,
             world_type, import_name, environment_type, handwritten_file_name,
             display_type, export_name)

        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
    else:
        main(steps, epoch_length,
             world_type, import_name, environment_type, handwritten_file_name,
             display_type, export_name)
