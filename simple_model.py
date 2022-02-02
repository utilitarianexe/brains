# could put this inside of the cell class maybe?
# Source is a function that takes step and determines if the synapse fired.
# voltage should be named potential everywhere
# should probably derive from a "potential generating" class or something
# synapse is a bad name.
class SimpleSynapse:
    def __init__(self, decay, step_size, starting_voltage, strength,
                 pre_cell=None,
                 post_cell=None,
                 artificial_source=None):
        self._decay = decay
        self._step_size = step_size
        self._voltage = starting_voltage
        self._strength = strength
        self._pre_cell = pre_cell
        self._post_cell = post_cell
        self._artificial_source = artificial_source

    def voltage(self):
        return self._voltage * self._strength

    def update(self, step):
        i = 0
        if self._artificial_source is not None:
            i += self._artificial_source(step)
        if self._pre_cell is not None:
            i += self._pre_cell.fired(step)
        if i > 0:
            self._voltage = i
        else:
            # need to think about step sizes
            self._voltage = self._voltage * (1 - self._decay)**self._step_size

class SimpleCell:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size):
        self._voltage_decay = voltage_decay
        self._membrane_voltage = starting_membrane_voltage
        self._step_size = step_size
        self._input_synapses = []
        self._fired = False # why not just check voltage

    def membrane_voltage(self, step):
        return self._membrane_voltage

    def fired(self, step):
        if self._fired:
            return 1
        else:
            return 0

    # I don't like this
    # should probably be a seperate membrane class
    def add_input_synapse(self, input_synapse):
        self._input_synapses.append(input_synapse)
    
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
            self._fired = True
        else:
            self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + input_voltage
            self._fired = False # maybe should be somewhere else


class SimpleModel:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input):
        self.name = "Simple Model"
        self.labels = ["~potential", "~input synapse current"]
        cell_a = SimpleCell(voltage_decay, input_decay, starting_membrane_voltage, step_size)
        cell_b = SimpleCell(voltage_decay, input_decay, starting_membrane_voltage, step_size)
        cell_fake_a_synapse = SimpleSynapse(input_decay, step_size, 0, 0.05, pre_cell=None,
                                       post_cell=cell_b,
                                       artificial_source=fake_input)

        cell_a_b_synapse = SimpleSynapse(input_decay, step_size, 0, 0.1, pre_cell=cell_a,
                                       post_cell=None,
                                       artificial_source=None)
        cell_a.add_input_synapse(cell_fake_a_synapse)
        cell_b.add_input_synapse(cell_a_b_synapse)
        self._cells = [cell_a, cell_b]
        self._fake_input = fake_input

    def step(self, step):
        for cell in self._cells:
            cell.update(step)
            
    def outputs(self, step):
        return {"cell a ": self._cells[0].membrane_voltage(step), "cell b": self._cells[1].membrane_voltage(step), "fake input": self._fake_input(step)}
