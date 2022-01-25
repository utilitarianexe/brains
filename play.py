import matplotlib.pyplot as plt

# to do
# adjust parameters without restarting
# multiple neurons
# get more backround on simulation generally(really need to retake calc)
# model class should be able to define what to output with names for several graphs
# i don't like how stateful this all is
# labeled arguments for constructors?

print("Its alive")

def graph_model(steps, model):
    outs_a = []
    outs_b = []
    for i in range(steps):
        model.step(i)
        out_a, out_b = model.output()
        outs_a.append(out_a)
        outs_b.append(out_b)
    plt.plot(outs_a, label=model.labels[0])
    plt.plot(outs_b, label=model.labels[1])
    plt.title(label=model.name,
              fontsize=40,
              color="green")
    plt.legend()
    #plt.ylabel('some numbers')
    plt.show()

class ExampleModel:
    def __init__(self):
        self.name = "Example Model"
        self.labels = ["increment", "zero"]
        self._x = 0

    def step(self, step):
        self._x = self._x + 1

    def output(self):
        return self._x, 0

class ElfCell:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input):
        self._fake_input = fake_input
        self._voltage_decay = voltage_decay
        self._input_decay = input_decay
        self._membrane_voltage = starting_membrane_voltage
        self._step_size = step_size
        self._fired = False # not even used?
        self._input_synapse = 0 # still a bad name

    def membrane_voltage(self):
        return self._membrane_voltage
    
    def input_synapse(self):
        return self._input_synapse
    
    def update_voltage(self):
        if self._membrane_voltage > 1:
            self._membrane_voltage = 0
        else:
            self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + self._input_synapse

    def update_input(self, step):
        i = self._fake_input(step)
        if i > 0:
            self._input_synapse = i
        else:
            self._input_synapse = self._input_synapse * (1 - self._input_decay)**self._step_size # need to think about step sizes



class ElfModel:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input):
        self.name = "Elf Model"
        self.labels = ["~potential", "~input synapse current"]
        self._input = 0
        self._cell = ElfCell(voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input)

    def step(self, step):
        self._cell.update_voltage()
        self._cell.update_input(step)
            
    def output(self):
        return self._cell.membrane_voltage(), self._cell.input_synapse()


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
            
    def output(self):
        return self._fast_potential, self._input

    
example_model = ExampleModel()
graph_model(100, example_model)

# Elf ##################
voltage_decay = 0.0001
input_decay = 0.001
#calcium_decay = 0.001
# it might make sense to drive a cell instead of a synapse
def fake_input_elf(step):
    if step % 50000 == 0 and step > 9999:
        return 0.002
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

    



