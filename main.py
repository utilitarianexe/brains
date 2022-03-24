import default_runs
import spirit_model
import example_model
import simple_model
import plot

import argparse

def run_model(model, steps, display):
    for i in range(steps):
        model.step(i)
        display.process_step()
    display.final_output()

def create_world():
    my_parser = argparse.ArgumentParser(description='Run brains')
    my_parser.add_argument('--display',
                           type=str,
                           choices=["pygame", "pyplot"],
                           help='How to display the model.')
    my_parser.add_argument('--model',
                           type=str,
                           choices=["spirit", "simple", "example", "handwritting"],
                           help='What model to use(well really the type of "run")')
    my_parser.add_argument('--steps',
                           type=int,
                           default=30000,
                           required=False,
                           help='Number of steps to run the model.')

    args = my_parser.parse_args()

    model_type = args.model
    model = None
    if model_type == "simple":
        model = default_runs.simple_model_stdp()
    elif model_type == "spirit":
        model = spirit_model.default_model()
    elif model_type == "example":
        model = default_runs.default_example_model()
    elif model_type == "handwritting":
        model = default_runs.simple_model_handwriting()

    display_type = args.display
    if display_type == "pygame":
        import game
        display = game.GameDisplay(model)
    elif display_type == "pyplot":
        import plot
        display = plot.PlotDisplay(model)

    steps = args.steps
    return model, steps, display

if __name__ == "__main__" :
    model, steps, display = create_world()
    run_model(model, steps, display)
