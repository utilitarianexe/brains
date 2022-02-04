import collections
from dataclasses import dataclass

@dataclass
class CellTypeParameters:
    voltage_decay: float
    current_decay: float
    starting_membrane_voltage: float

@dataclass
class SynapseTypeParameters:
    starting_strength: float

@dataclass
class PerCellParameters:
    name: str
    x_position: int
    y_position: int

@dataclass
class PerSynapseParameters:
    pre_cell_name: str
    post_cell_name: str

@dataclass
class NetworkDefinition:
    per_cell_parameters: list
    per_synapse_parameters: list
    cell_name_with_fake_input: str


# voltage should be named potential everywhere
# current is also wrong(could be delta potential but thats not quite right either)
# should probably derive from a "potential generating" class or something
# synapse and cell body are sort of bad names as they don't match one to one with the bio
# fix tests
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
        
    def membrane_voltage(self):
        return self._membrane_voltage

    def fired(self):
        return self._fired

    def update(self):
        # need to think about step sizes
        self.input_current = self.input_current * (1 - self._current_decay)**self._step_size
        self._membrane_voltage = self._membrane_voltage * (1 - self._voltage_decay)**self._step_size + self.input_current * self._step_size
        self._fired = False

        # magic numbers
        if self._membrane_voltage > 1:
            self._membrane_voltage = -1
            self._fired = True

class Cell:
    def __init__(self, name, x_position, y_position,
                 cell_body, input_synapses, output_synapses,
                 artificial_source=None):
        self.name = name
        self.x_position = x_position
        self.y_position = y_position
        
        # I don't like the coupling causing these to be public
        self.input_synapses = input_synapses # not acutally used yet
        self.output_synapses = output_synapses
        self.cell_body = cell_body
        
        self._artificial_source = artificial_source

    def membrane_voltage(self):
        return self.cell_body.membrane_voltage()

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
    
class SimpleModel:
    def __init__(self,  cell_parameters, synapse_parameters, network_definition, step_size,
                 fake_input):
        self.name = "Simple Model"
        self._cells = SimpleModel._build_network(cell_parameters, synapse_parameters,
                                                 network_definition,
                                                 step_size,
                                                 fake_input)

    def step(self, step):
        # need to do in feed forward order
        for cell in self._cells:
            cell.update(step)

    def video_output(self):
        drawables = []
        for cell in self._cells:
            # maybe make a class
            drawable = {"name": cell.name,
                        "x": cell.x_position, "y": cell.y_position,
                        "strength": cell.membrane_voltage()}
            drawables.append(drawable)
        return drawables


    def outputs(self):
        output = {}
        for cell in self._cells:
            output[cell.name] = cell.membrane_voltage()
        return output


    # will need ways to verify the network
    # need to gate submits with tests
    # conform to style guide
    # need tests and visulization
    # are there other places we are using self for no reason, how do we name these
    def _build_network(cell_type_parameters,
                       synapse_type_parameters,
                       network_definition,
                       step_size,
                       fake_input):
        cells_by_name = {}
        cells = []
        for cell_parameters in network_definition.per_cell_parameters:
            name = cell_parameters.name
            cell_body = CellBody(cell_type_parameters.voltage_decay,
                                 cell_type_parameters.current_decay,
                                 cell_type_parameters.starting_membrane_voltage,
                                 step_size)
            # ugly should not need if, use input parameter stuff
            if name != network_definition.cell_name_with_fake_input:
                cell = Cell(name,
                            cell_parameters.x_position,
                            cell_parameters.y_position,
                            cell_body, [], [])
            else:
                cell = Cell(name,
                            cell_parameters.x_position,
                            cell_parameters.y_position,
                            cell_body, [], [], fake_input)
            cells_by_name[name] = cell
            cells.append(cell)

        for synapse_parameters in network_definition.per_synapse_parameters:
            pre_cell = cells_by_name[synapse_parameters.pre_cell_name]
            post_cell = cells_by_name[synapse_parameters.post_cell_name]
            synapse  = Synapse(synapse_type_parameters.starting_strength, pre_cell, post_cell)
            pre_cell.output_synapses.append(synapse)
            post_cell.input_synapses.append(synapse)

        return cells

# too much display stuff in here. should do position else where maybe?
# or will position every matter to to the model and not be pure display?
# maybe compromise and do grid position here and the rest in display
def default_network():
    cell_name_and_grid_position = [("a", (0, 0)),
                                   ("b", (1, 0)),
                                   ("c", (2, 0)), ("d", (2, 1)),
                                   ("e", (3, 0))]
    synapse_end_points = [("a", "b"),
                          ("b", "c"),
                          ("b", "d"),
                          ("c", "e"),
                          ("d", "e"),]
    cell_name_with_fake_input = "a"

    # dont like how we are doing plurals
    per_cell_parameters = []

    # all this should be in display class
    x_spacing = 10
    y_spacing = 2
    border = 5
    height = 20
    width = 20
    for (cell_name, (x_grid_pos, y_grid_pos)) in cell_name_and_grid_position:
        x_position = x_grid_pos * ( width + x_spacing) + border
        y_position = y_grid_pos * (height + y_spacing) + border
        cell_parameters = PerCellParameters(cell_name, x_position, y_position)
        per_cell_parameters.append(cell_parameters)

    per_synapse_parameters = []
    for (pre_cell_name, post_cell_name) in synapse_end_points:
        per_synapse_parameters.append(PerSynapseParameters(pre_cell_name, post_cell_name))
        
    return NetworkDefinition(per_cell_parameters,
                             per_synapse_parameters,
                             cell_name_with_fake_input)


def default_model():
    voltage_decay = 0.01
    input_decay = 0.1
    step_size = 1
    starting_synapse_strength = 0.15
    cell_type_parameters = CellTypeParameters(voltage_decay, input_decay, 0)
    synapse_type_parameters = SynapseTypeParameters(starting_synapse_strength)
    network_definition = default_network()


    def fake_input_simple(step):
        if step % 50000 == 200 and step > 0:
            return 0.15
        return 0
    return SimpleModel(cell_type_parameters, synapse_type_parameters,
                       network_definition,
                       step_size, fake_input_simple)
    
