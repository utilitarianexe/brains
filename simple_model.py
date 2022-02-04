import collections

# voltage should be named potential everywhere
# current is also wrong
# should probably derive from a "potential generating" class or something
# synapse is a bad name.
# fix test
class Synapse:
    def __init__(self, strength, pre_cell, post_cell):
        self.strength = strength
        self.pre_cell = pre_cell
        self.post_cell = post_cell

class CellBody:
    def __init__(self, voltage_decay, current_decay, starting_membrane_voltage, step_size):
        self._voltage_decay = voltage_decay
        self._current_decay = current_decay
        self._membrane_voltage = starting_membrane_voltage

        #don't really like that this is public
        self.input_current = 0
        self._step_size = step_size
        self._fired = False # why not just check voltage
        
    def membrane_voltage(self, step):
        return self._membrane_voltage

    def fired(self):
        return self._fired

    def update(self):
        # need to think about step sizes
        self.input_current = self.input_current * (1 - self._current_decay)**self._step_size
        self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + self.input_current * self._step_size
        self._fired = False
        
        if self._membrane_voltage > 1:
            self._membrane_voltage = -1
            self._fired = True

class Cell:
    def __init__(self, name, cell_body, input_synapses, output_synapses, artificial_source=None):
        self.name = name
        # I don't like the coupling causing these to be public
        self.input_synapses = input_synapses # not acutally used yet
        self.output_synapses = output_synapses

        # don't like that this is public
        self.cell_body = cell_body
        self._artificial_source = artificial_source

    def membrane_voltage(self, step):
        return self.cell_body.membrane_voltage(step)

    def _apply_fire(self):
        for synapse in self.output_synapses:
            # ugly
            synapse.post_cell.cell_body.input_current += synapse.strength

    def update(self, step):
        if self._artificial_source is not None:
            self.cell_body.input_current += self._artificial_source(step)
            
        self.cell_body.update()
        if self.cell_body.fired():
            self._apply_fire()


# make a dataclass
class CellParameters:
    def __init__(self, voltage_decay, current_decay, starting_membrane_voltage):
        self.voltage_decay = voltage_decay
        self.current_decay = current_decay
        self.starting_membrane_voltage = starting_membrane_voltage

class SynapseParameters:
    def __init__(self, strength):
        self.strength = strength

class NetworkDefinition:
    def __init__(self, cell_names, synapse_names, fake_input_location):
        self.cell_names = cell_names
        self.synapse_names = synapse_names
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
    # need tests and visulization
    # are there other places we are using self for no reason, how do we name these
    def _build_network(cell_parameters, synapse_parameters,
                       network_definition,
                       step_size,
                       fake_input):
        cells = {}
        for cell_name in network_definition.cell_names:
            cell_body = CellBody(cell_parameters.voltage_decay,
                                 cell_parameters.current_decay,
                                 cell_parameters.starting_membrane_voltage,
                                 step_size)
            # ugly should not need if, use input parameter stuff
            if cell_name != network_definition.fake_input_location:
                cell = Cell(cell_name, cell_body, [], [])
            else:
                cell = Cell(cell_name, cell_body, [], [], fake_input)
            cells[cell_name] = cell

        for synapse_name in network_definition.synapse_names:
            pre_cell_name = synapse_name[0]
            post_cell_name = synapse_name[1]
            pre_cell = cells[pre_cell_name]
            post_cell = cells[post_cell_name]
            synapse  = Synapse(synapse_parameters.strength, pre_cell, post_cell)
            pre_cell.output_synapses.append(synapse)
            post_cell.input_synapses.append(synapse)

        return cells

    def step(self, step):
        # need to do in feed forward order
        for cell in self._cells.values():
            cell.update(step)

    # step is probably not needed
    def outputs(self, step):
        output = {}
        for cell in self._cells.values():
            output[cell.name] = cell.membrane_voltage(step)
        return output
    
