import network
from network import Layout

import collections
from dataclasses import dataclass

@dataclass
class CellTypeParameters:
    voltage_decay: float
    current_decay: float
    starting_membrane_voltage: float

@dataclass
class SynapseTypeParameters:
    # not actually used
    starting_strength: float


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
    def __init__(self, id, x_grid_position, y_grid_position,
                 cell_body, input_synapses, output_synapses,
                 artificial_source=None):
        self.id = id
        self.x_grid_position = x_grid_position
        self.y_grid_position = y_grid_position
        
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
            drawable = {"id": cell.id,
                        "x": cell.x_grid_position, "y": cell.y_grid_position,
                        "strength": cell.membrane_voltage()}
            drawables.append(drawable)
        return drawables


    def outputs(self):
        output = {}
        for cell in self._cells:
            output[cell.id] = cell.membrane_voltage()
        return output


    # will need ways to verify the network
    # are there other places we are using self for no reason, how do we name these
    def _build_network(cell_type_parameters,
                       synapse_type_parameters,
                       network_definition,
                       step_size,
                       fake_input):
        cells_by_id = {}
        cells = []
        for cell_parameters in network_definition.per_cell_parameters:
            id = cell_parameters.id
            cell_body = CellBody(cell_type_parameters.voltage_decay,
                                 cell_type_parameters.current_decay,
                                 cell_type_parameters.starting_membrane_voltage,
                                 step_size)
            # ugly should not need if, use input parameter stuff
            if id != network_definition.cell_id_with_fake_input:
                cell = Cell(id,
                            cell_parameters.x_grid_position,
                            cell_parameters.y_grid_position,
                            cell_body, [], [])
            else:
                cell = Cell(id,
                            cell_parameters.x_grid_position,
                            cell_parameters.y_grid_position,
                            cell_body, [], [], fake_input)
            cells_by_id[id] = cell
            cells.append(cell)

        for synapse_parameters in network_definition.per_synapse_parameters:
            pre_cell = cells_by_id[synapse_parameters.pre_cell_id]
            post_cell = cells_by_id[synapse_parameters.post_cell_id]
            synapse  = Synapse(synapse_parameters.starting_strength, pre_cell, post_cell)
            pre_cell.output_synapses.append(synapse)
            post_cell.input_synapses.append(synapse)

        return cells


def small_default_network():
    cell_id_and_grid_positions = [("a", (0, 0)),
                                   ("b", (1, 0)),
                                   ("c", (2, 0)), ("d", (2, 1)),
                                   ("e", (3, 0))]
    synapse_end_points = [("a", "b", 0.15),
                          ("b", "c", 0.15),
                          ("b", "d", 0.15),
                          ("c", "e", 0.15),
                          ("d", "e", 0.15),]
    cell_id_with_fake_input = "a"
    return network_from_edge_list(cell_id_and_grid_positions,
                                  synapse_end_points,
                                  cell_id_with_fake_input)


def layer_based_default_network():
    layers = [("a", 9, Layout.SQUARE),
              ("b", 20, Layout.LINE),
              ("c", 20, Layout.LINE),
              ("d", 15, Layout.SQUARE),
              ("e", 10, Layout.LINE)]
    
    # Something about connection probability rubs me wrong.
    # strengths random
    # connections might be more complex
    layer_connections = [("a", "b", 1, 0.15), ("b", "c", 0.2, 0.05),
                         ("c", "d", 1, 0.01), ("d", "e", 1, 0.15)]
    cell_id_with_fake_input = ("a", 0,)
    return network.build_layer_based_network(layers, layer_connections, cell_id_with_fake_input)

def default_model():
    voltage_decay = 0.01
    input_decay = 0.1
    step_size = 1

    # not actually used
    starting_synapse_strength = 0.15
    
    cell_type_parameters = CellTypeParameters(voltage_decay, input_decay, 0)
    synapse_type_parameters = SynapseTypeParameters(starting_synapse_strength)
    network_definition = layer_based_default_network()


    def fake_input_simple(step):
        if step % 50000 == 200 and step > 0:
            return 0.15
        return 0
    return SimpleModel(cell_type_parameters, synapse_type_parameters,
                       network_definition,
                       step_size, fake_input_simple)
    
