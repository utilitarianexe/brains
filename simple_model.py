from utils import decay

import collections
from dataclasses import dataclass

@dataclass
class CellTypeParameters:
    voltage_decay: float
    current_decay: float
    calcium_decay: float
    starting_membrane_voltage: float
    max_voltage: float
    voltage_reset: float
    calcium_increment: float
    input_current_reset: float
    starting_calcium: float
    starting_input_current: float
    reset_input_current: bool

@dataclass
class SynapseTypeParameters:
    stdp_scalar: float
    reward_scalar: float
    max_strength: float
    min_strength: float
    s_tag_decay_rate: float
    starting_s_tag: float

@dataclass
class ModelParameters:
    step_size: int
    starting_dopamine: float
    dopamine_decay: float
    cell_type_parameters: CellTypeParameters
    synapse_type_parameters: SynapseTypeParameters
    
    
# voltage and current should be named potential everywhere
# should probably derive from a "potential generating" class or something
class Synapse:
    def __init__(self, pre_cell, post_cell,
                 synapse_definition, step_size,
                 synapse_type_parameters):
        self.pre_cell = pre_cell
        self.post_cell = post_cell

        # much of this could be private
        self.strength = synapse_definition.starting_strength
        self.step_size = step_size

        # can be though of as recording the firing pattern correlation
        self.s_tag = synapse_type_parameters.starting_s_tag
        self.stdp_scalar = synapse_type_parameters.stdp_scalar
        self.reward_scalar = synapse_type_parameters.reward_scalar
        self.max_strength = synapse_type_parameters.max_strength
        self.min_strength = synapse_type_parameters.min_strength
        self.s_tag_decay_rate = synapse_type_parameters.s_tag_decay_rate

    def update(self, dopamine):
        self.stdp()
        self.train(dopamine)

    def train(self, dopamine):
        self.strength += self.s_tag * dopamine * self.reward_scalar
        if self.strength >= self.max_strength:
            self.strength = self.max_strength
        if self.strength < self.min_strength:
            self.strength = self.min_strength
            
    def stdp(self):
        self.s_tag = decay(self.s_tag, self.s_tag_decay_rate, self.step_size)
        
        if self.pre_cell.fired():
            self.s_tag -= self.stdp_scalar * self.post_cell.calcium()
        if self.post_cell.fired():
            self.s_tag += self.stdp_scalar * self.pre_cell.calcium()

class CellMembrane:
    def __init__(self, cell_type_parameters, step_size):
        self._voltage_decay = cell_type_parameters.voltage_decay
        self._current_decay = cell_type_parameters.current_decay
        self._calcium_decay = cell_type_parameters.calcium_decay
        self._voltage = cell_type_parameters.starting_membrane_voltage
        self._input_current = cell_type_parameters.starting_input_current
        self._calcium = cell_type_parameters.starting_calcium
        self._max_voltage = cell_type_parameters.max_voltage
        self._voltage_reset = cell_type_parameters.voltage_reset
        self._calcium_increment = cell_type_parameters.calcium_increment
        self._input_current_reset = cell_type_parameters.input_current_reset
        self._reset_input_current = cell_type_parameters.reset_input_current
        
        self._step_size = step_size
        self._fired = False # why not just check voltage

    def calcium(self):
        return self._calcium
        
    def voltage(self):
        return self._voltage

    def fired(self):
        return self._fired

    def input_current(self):
        return self._input_current

    def receive_input(self, strength):
        self._input_current += strength

    def update(self):
        '''
           Voltage and input tend to 0 from both the negative and positive side.
           Changing by higher absalute values the further from 0 they are.

           If voltage gets above one the cell fires and is set to -1
           Input never resets. It just gets added to or decays.

           Calcium increases after firing as a sort of history of recent firing.
        '''
        self._fired = False
        if self._voltage > self._max_voltage:
            self._voltage = self._voltage_reset
            self._fired = True
            self._calcium += self._calcium_increment
            if self._reset_input_current:
                self._input_current =self._input_current_reset

        self._voltage = decay(self._voltage, self._voltage_decay, self._step_size)
        self._voltage += self._input_current * self._step_size
        self._input_current = decay(self._input_current, self._current_decay, self._step_size)
        self._calcium = decay(self._calcium, self._calcium_decay, self._step_size)

class Cell:
    def __init__(self, cell_definition, cell_membrane,
                 input_synapses, output_synapses,
                 environment):
        self.uuid = cell_definition.uuid
        self.label = cell_definition.label
        self._layer_id = cell_definition.layer_id
        self._cell_number = cell_definition.cell_number
        self.x_grid_position = cell_definition.x_grid_position
        self.y_grid_position = cell_definition.y_grid_position
        self._environment = environment
        
        # I don't like the coupling causing these to be public
        self.input_synapses = input_synapses # not acutally used yet
        self.output_synapses = output_synapses
        self._cell_membrane = cell_membrane

    # these should be named as getters and maybe use the auto thing
    # or maybe one cell class
    # or maybe make a cell membrane getter function
    def membrane_voltage(self):
        return self._cell_membrane.voltage()

    def calcium(self):
        return self._cell_membrane.calcium()
    
    def input_current(self):
        return self._cell_membrane.input_current()

    def fired(self):
        return self._cell_membrane.fired()

    def receive_fire(self, strength):
        self._cell_membrane.receive_input(strength)

    def apply_fire(self):
        if self._cell_membrane.fired():
            for synapse in self.output_synapses:
                synapse.post_cell.receive_fire(synapse.strength)

    def update(self, step):
        outside_current = self._environment.potential_from_location(step,
                                                                    self.x_grid_position,
                                                                    self.y_grid_position)
        self._cell_membrane.receive_input(outside_current)
        self._cell_membrane.update()
    
class SimpleModel:
    def __init__(self, network_definition, environment,
                 model_parameters):
        self.name = "Simple Model"
        self._environment = environment
        self._dopamine = model_parameters.starting_dopamine
        self._dopamine_decay = model_parameters.dopamine_decay
        self._step_size = model_parameters.step_size
        self._cells, self.synapses = self._build_network(model_parameters.cell_type_parameters,
                                                        model_parameters.synapse_type_parameters,
                                                        network_definition,
                                                        self._step_size)

    def update_dopamine(self, step):
        self._dopamine = decay(self._dopamine, self._dopamine_decay, self._step_size)
        for cell in self._cells:
            if cell.fired():
                if self._environment.reward(step, cell._layer_id, cell._cell_number):
                    # magic
                    self._dopamine += 1

    def step(self, step):
        for cell in self._cells:
            cell.update(step)

        for cell in self._cells:
            cell.apply_fire()

        self.update_dopamine(step)

        for synapse in self.synapses:
            synapse.update(self._dopamine)

    def video_output(self):
        drawables = []
        for cell in self._cells:
            # maybe make a class
            drawable = {"id": cell.label,
                        "x": cell.x_grid_position, "y": cell.y_grid_position,
                        "strength": cell.membrane_voltage()}
            drawables.append(drawable)
        texts = ["dopamine: " + str(round(self._dopamine, 4))]
        return (drawables, texts)

    def outputs(self):
        output = {}
        for cell in self._cells:
            output[cell.label] = cell.membrane_voltage()
            if cell.label == 'c':
                output['c input'] = cell.input_current()

        # magic output this should be defined in the default file?
        for synapse in self.synapses:
            if synapse.pre_cell.label == "a" and synapse.post_cell.label == "c":
                output["a c synapse"] = synapse.strength
            if synapse.pre_cell.label == "b" and synapse.post_cell.label == "c":
                output["b c synapse"] = synapse.strength
        return output

    # will need ways to verify the network
    # should this be in the network module
    def _build_network(self, cell_type_parameters,
                       synapse_type_parameters,
                       network_definition,
                       step_size):
        cells_by_id = {}
        cells = []
        for cell_definition in network_definition.cell_definitions:
            cell_membrane = CellMembrane(cell_type_parameters, step_size)
            cell = Cell(cell_definition, cell_membrane,
                        [], [], self._environment)
            cells_by_id[cell.uuid] = cell
            cells.append(cell)

        synapses = []
        for synapse_definition in network_definition.synapse_definitions:
            pre_cell = cells_by_id[synapse_definition.pre_cell_id]
            post_cell = cells_by_id[synapse_definition.post_cell_id]
            synapse = Synapse(pre_cell, post_cell,
                              synapse_definition,
                              step_size,
                              synapse_type_parameters)
            synapses.append(synapse)
            pre_cell.output_synapses.append(synapse)
            post_cell.input_synapses.append(synapse)

        return cells, synapses
