import matplotlib.pyplot as plt
import collections
import simple_model
import spirit_model

# to do
# adjust parameters without restarting
# multiple neurons
# get more backround on simulation generally(really need to retake calc)
# model class should be able to define what to output with names for several graphs
# i don't like how stateful this all is
# labeled arguments for constructors?

print("Its alive")

def graph_model(steps, model):
    lines = collections.defaultdict(list)
    for i in range(steps):
        model.step(i)
        outputs = model.outputs(i)
        for label, value in outputs.items():
            lines[label].append(value)
    for label, values in lines.items():
        plt.plot(values, label=label)
    plt.title(label=model.name,
              fontsize=40,
              color="green")
    plt.legend()
    plt.show()

class ExampleModel:
    def __init__(self):
        self.name = "Example Model"
        self._x = 0

    def step(self, step):
        self._x = self._x + 1

    def outputs(self, i):
        #spelling?
        return {"increment": self._x, "constant": 0}

def run_example():
    example_model = ExampleModel()
    graph_model(100, example_model)

# omg spell check
def run_simple():
    voltage_decay = 0.01
    input_decay = 0.1
    step_size = 1
    starting_synapse_strength = 0.15
    cell_parameters = simple_model.CellParameters(voltage_decay, input_decay, 0)
    synapse_parameters = simple_model.SynapseParameters(starting_synapse_strength)
    cell_names = ["a", "b", "c", "d", "e"]
    # named would be better than positional
    synapse_names = [("a", "b"),
                           ("b", "c"),
                           ("b", "d"),
                           ("c", "e"),
                           ("d", "e"),]
    fake_input_location = "a"
    network_definition = simple_model.NetworkDefinition(cell_names,
                                                        synapse_names,
                                                        fake_input_location)


    def fake_input_simple(step):
        if step % 50000 == 200 and step > 0:
            return 0.15
        return 0
    simple = simple_model.SimpleModel(cell_parameters, synapse_parameters, network_definition,
                                      step_size, fake_input_simple)
    graph_model(1000, simple)


def run_spirit():
    alpha = 1
    mu = 0.001
    sigma = 0
    sigma_next = 0
    input_decay = 0.001
    # it might make sense to drive a cell instead of a synapse
    def fake_input_spirit(step):
        if step % 10000 == 0 and step > 9999:
            return 1
        return 0
    spirit = spirit_model.SpiritModel(input_decay, alpha, mu, sigma, sigma_next, fake_input_spirit)
    graph_model(100000, spirit)

def main():
    # run_example()
    run_simple()
    # run_spirit()

if __name__ == '__main__':
    main()
