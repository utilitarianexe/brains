import matplotlib.pyplot as plt
import collections

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

# could put this inside of the cell class maybe?
# Source is a function that takes step and determines if the synapse fired. 
class ElfSynapse:
    def __init__(self, decay, step_size, starting_voltage, source):
        self._decay = decay
        self._step_size = step_size
        self._source = source
        self._voltage = starting_voltage

    def voltage(self):
        return self._voltage

    def update(self, step):
        i = self._source(step)
        if i > 0:
            self._voltage = i
        else:
            self._voltage = self._voltage * (1 - self._decay)**self._step_size # need to think about step sizes
        

class ElfCell:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, input_sources):
        self._voltage_decay = voltage_decay
        self._membrane_voltage = starting_membrane_voltage
        self._step_size = step_size
        self._input_synapses = []
        for input_source in input_sources:
            self._input_synapses.append(ElfSynapse(input_decay, step_size, 0, input_source))
        self.fired = False # why not just check voltage

    def membrane_voltage(self, step):
        return self._membrane_voltage
    
    def update(self, step):
        # volts should just be called potential i think
        # does order matter here
        # synaptic delay?
        total_input_voltage = 0
        for input_synapse in self._input_synapses:
            input_synapse.update(step)
            total_input_voltage += input_synapse.voltage()
        self._update_voltage(total_input_voltage)
    
    def _update_voltage(self, input_voltage):
        if self._membrane_voltage > 1:
            self._membrane_voltage = 0
            self.fired = True
        else:
            # magic input scaling needs fixed
            self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + input_voltage * 0.001
            self.fired = False # maybe should be somewhere else


class ElfModel:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input):
        self.name = "Elf Model"
        self.labels = ["~potential", "~input synapse current"]
        cell_a = ElfCell(voltage_decay, input_decay, starting_membrane_voltage, step_size, [fake_input])
        cell_b = ElfCell(voltage_decay, input_decay, starting_membrane_voltage, step_size, [cell_a.membrane_voltage])
        self._cells = [cell_a, cell_b]
        self._fake_input = fake_input

    def step(self, step):
        for cell in self._cells:
            cell.update(step)
            
    def outputs(self, step):
        return {"cell 0 ": self._cells[0].membrane_voltage(step), "cell 1": self._cells[1].membrane_voltage(step), "fake input": self._fake_input(step)}


##### from paper
# each if should be a function name.
# map to variables in paper
# map to ~ chemical channels
# why do we use I for slow potential if that is current(I guess leak current is a potential?). The old paper just calls it y.
# is what I think slow potential really a potential. I it summed with the fast one?
# spikes are single points
# should produce bursts of spikes with the right parameters
# wtf should the ranges be
class SpiritModel():
    def __init__(self, input_decay, alpha, mu, sigma, sigma_next, fake_input):
        self.name = "Spirit Model"
        self.labels = ["~potential", "~input synapse current"]
        self._input_decay = input_decay
        self._alpha = alpha
        self._mu = mu
        self._sigma = sigma
        self._sigma_next = sigma_next
        self._input = 0 # will become array? well many cells anyway.

        self._fast_potential = -0.5
        self._fast_potential_previous = -0.5
        self._slow_potential = -0.5
        self._step_size = 1 #?
        self._fake_input = fake_input

    #acutally should take u as input which is slow_potential + input
    def _next_fast_potential(self, fast_potential, previous_fast_potential, slow_potential, u):
        # if you are under 0 increase. Slower the more negative you start.
        if fast_potential <= 0:
            return self._alpha/(1 - fast_potential)  + u

        #spike if you are over 0 to some set point. but don't if you are already spiked. Should I use u here
        if fast_potential > 0 and fast_potential < alpha + slow_potential and previous_fast_potential <= 0: #why previous?
            return self._alpha + slow_potential

        # if you spike fall back on the next step
        if self._alpha + slow_potential <= fast_potential or previous_fast_potential > 0:
            return -1
        print("fail") # make an exception
        return 0

    # mu should be low to make this change slowly    
    def _next_slow_potential(self, fast_potential, slow_potential):
        return slow_potential - self._mu*(fast_potential + 1) + self._mu*self._sigma + self._mu*self._sigma_next # wtf do we have sigma and sigma next

    def _update_voltage(self):
        self._fast_potential = self._next_fast_potential(self._fast_potential, self._fast_potential_previous, self._slow_potential, self._slow_potential + self._input)
        self._fast_potential_previous = self._fast_potential
        self._slow_potential = self._next_slow_potential(self._fast_potential, self._slow_potential)

    # this is kinda made up need to look at paper
    def _update_input(self, step):
        i = self._fake_input(step)
        if i > 0:
            self._input = i
        else:
            self._input = self._input * (1 - self._input_decay)**self._step_size + i
    
    def step(self, step):
        self._update_voltage()
        self._update_input(step)
            
    def outputs(self, step):
        return {"potential": self._fast_potential, "input synapse": self._input}

    
example_model = ExampleModel()
graph_model(100, example_model)

# Elf ##################
voltage_decay = 0.0001
input_decay = 0.001
#calcium_decay = 0.001
# it might make sense to drive a cell instead of a synapse
def fake_input_elf(step):
    if step % 50000 == 0 and step > 9999:
        return 2
    return 0
elf_model = ElfModel(voltage_decay, input_decay, 0.0, 1, fake_input_elf)
graph_model(500000, elf_model)


# Spirit ################
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
spirit_model = SpiritModel(input_decay, alpha, mu, sigma, sigma_next, fake_input_spirit)
graph_model(100000, spirit_model)

    



