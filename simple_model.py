import collections

# could put this inside of the cell class maybe?
# Source is a function that takes step and determines if the synapse fired.
# voltage should be named potential everywhere
# should probably derive from a "potential generating" class or something
# synapse is a bad name.
class SimpleSynapse:
    def __init__(self, decay, starting_voltage, strength, step_size,):
        self._decay = decay
        self._step_size = step_size
        self._voltage = starting_voltage
        self._strength = strength

    def voltage(self):
        return self._voltage * self._strength

    def update(self, activate):
        if activate:
            self._voltage = 1
        else:
            # need to think about step sizes
            self._voltage = self._voltage * (1 - self._decay)**self._step_size

class CellBody:
    def __init__(self, voltage_decay, starting_membrane_voltage, step_size):
        self._voltage_decay = voltage_decay
        self._membrane_voltage = starting_membrane_voltage
        self._step_size = step_size
        self._fired = False # why not just check voltage
        
    def membrane_voltage(self, step):
        return self._membrane_voltage

    def fired(self):
        if self._fired:
            return 1
        else:
            return 0
        
    def update_voltage(self, input_voltage):
        if self._membrane_voltage > 1:
            self._membrane_voltage = 0
            self._fired = True
        else:
            self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + input_voltage
            self._fired = False # maybe should be somewhere else


class SimpleCell:
    def __init__(self, name, cell_body, input_synapses, output_synapses, artificial_source=None):
        self.name = name
        self._cell_body = cell_body
        self._input_synapses = input_synapses
        self._output_synapses = output_synapses
        self._artificial_source = artificial_source

    def membrane_voltage(self, step):
        return self._cell_body.membrane_voltage(step)

    def fired(self):
        return self._cell_body.fired()

    def update(self, step):
        # volts should just be called potential i think
        # does order matter here
        # synaptic delay?
            
        total_input_voltage = 0
        for input_synapse in self._input_synapses:
            total_input_voltage += input_synapse.voltage()
        if self._artificial_source is not None:
            total_input_voltage += self._artificial_source(step)
        self._cell_body.update_voltage(total_input_voltage)
        for output_synapse in self._output_synapses:
            if self.fired():
                output_synapse.update(True)
            else:
                output_synapse.update(False)

# make a dataclass
class CellParameters:
    def __init__(self, voltage_decay, starting_membrane_voltage):
        self.voltage_decay = voltage_decay
        self.starting_membrane_voltage = starting_membrane_voltage

class SynapseParameters:
    def __init__(self, decay, starting_voltage, strength):
        self.decay = decay
        self.starting_voltage = starting_voltage
        self.strength = strength

class NetworkDefinition:
    def __init__(self, cell_definitions, synapse_definitions, fake_input_location):
        self.cell_definitions = cell_definitions
        self.synapse_definitions = synapse_definitions
        self.fake_input_location = fake_input_location

    
class SimpleModel:
    def __init__(self,  cell_parameters, synapse_parameters, network_definition, step_size,
                 fake_input):
        self.name = "Simple Model"
        self._cells = SimpleModel._build_network(cell_parameters, synapse_parameters,
                                                 network_definition,
                                                 step_size,
                                                 fake_input)

    # will need ways to verify the network
    # need to gate submits with tests
    # conform to style guide
    # probably want some kind of cell and synapse parameters classes
    # need tests and visulization
    # are there other places we are using self for no reason, how do we name these
    def _build_network(cell_parameters, synapse_parameters,
                       network_definition,
                       step_size,
                       fake_input):
        # ugly
        cell_bodies = {}
        for cell_definition in network_definition.cell_definitions:
            cell_body = CellBody(cell_parameters.voltage_decay,
                                 cell_parameters.starting_membrane_voltage,
                                 step_size)
            cell_bodies[cell_definition] = cell_body

        output_synapses = collections.defaultdict(list)
        input_synapses = collections.defaultdict(list)
        for synapse_definition in network_definition.synapse_definitions:
            # magic number
            synapse  = SimpleSynapse(synapse_parameters.decay,
                                     synapse_parameters.starting_voltage,
                                     synapse_parameters.strength, step_size)
            output_synapses[synapse_definition[0]].append(synapse)
            input_synapses[synapse_definition[1]].append(synapse)

        cells = []
        for cell_definition, cell_body in cell_bodies.items():
            if cell_definition != network_definition.fake_input_location:
                cell = SimpleCell(cell_definition, cell_body, input_synapses[cell_definition],
                                  output_synapses[cell_definition])
            else:
                cell = SimpleCell(cell_definition, cell_body, input_synapses[cell_definition],
                                  output_synapses[cell_definition], fake_input)
            cells.append(cell)
        return cells


    def step(self, step):
        for cell in self._cells:
            cell.update(step)

    # step is probably not needed
    def outputs(self, step):
        output = {}
        for cell in self._cells:
            output[cell.name] = cell.membrane_voltage(step)
        return output
    
