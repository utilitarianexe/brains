# could put this inside of the cell class maybe?
# Source is a function that takes step and determines if the synapse fired. 
class SimpleSynapse:
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
        

class SimpleCell:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, input_sources):
        self._voltage_decay = voltage_decay
        self._membrane_voltage = starting_membrane_voltage
        self._step_size = step_size
        self._input_synapses = []
        for input_source in input_sources:
            self._input_synapses.append(SimpleSynapse(input_decay, step_size, 0, input_source))
        self._fired = False # why not just check voltage

    def membrane_voltage(self, step):
        return self._membrane_voltage

    def fired(self, step):
        if self._fired:
            return 1
        else:
            return 0
    
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
            # magic input scaling needs fixed
            self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + input_voltage * 0.001
            self._fired = False # maybe should be somewhere else


class SimpleModel:
    def __init__(self, voltage_decay, input_decay, starting_membrane_voltage, step_size, fake_input):
        self.name = "Simple Model"
        self.labels = ["~potential", "~input synapse current"]
        cell_a = SimpleCell(voltage_decay, input_decay, starting_membrane_voltage, step_size, [fake_input])
        cell_b = SimpleCell(voltage_decay, input_decay, starting_membrane_voltage, step_size, [cell_a.fired])
        self._cells = [cell_a, cell_b]
        self._fake_input = fake_input

    def step(self, step):
        for cell in self._cells:
            cell.update(step)
            
    def outputs(self, step):
        return {"cell 0 ": self._cells[0].membrane_voltage(step), "cell 1": self._cells[1].membrane_voltage(step), "fake input": self._fake_input(step)}
