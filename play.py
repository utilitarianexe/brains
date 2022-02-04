import matplotlib.pyplot as plt
import collections
import simple_model
import spirit_model
import example_model

# to do
# adjust parameters without restarting
# multiple neurons
# get more backround on simulation generally(really need to retake calc)
# model class should be able to define what to output with names for several graphs
# i don't like how stateful this all is
# labeled arguments for constructors?

print("Its alive")

def graph_model(model, steps):
    lines = collections.defaultdict(list)
    for i in range(steps):
        model.step(i)
        outputs = model.outputs()
        for label, value in outputs.items():
            lines[label].append(value)
    for label, values in lines.items():
        plt.plot(values, label=label)
    plt.title(label=model.name,
              fontsize=40,
              color="green")
    plt.legend()
    plt.show()


def run_example():
    model = example_model.default_model()
    graph_model(model, 100)

# omg spell check
def run_simple():
    simple = simple_model.default_model()
    graph_model(simple, 1000)


def run_spirit():
    spirit = spirit_model.default_model()
    graph_model(spirit, 100000)

# if we were cool we could plot and pygame
def main():
    # run_example()
    run_simple()
    # run_spirit()

if __name__ == '__main__':
    main()
