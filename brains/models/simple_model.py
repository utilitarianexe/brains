from brains.utils import decay
from brains.network import SynapseDefinition, NetworkDefinition

from collections import defaultdict
from dataclasses import dataclass, asdict
import random

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
    input_balance: bool

def stdp_cell_type_parameters(input_balance):
    return CellTypeParameters(voltage_decay=0.01,
                              current_decay=0.03,
                              calcium_decay=0.1,
                              starting_membrane_voltage=0.0,
                              max_voltage=1.0,
                              voltage_reset=-1.0,
                              calcium_increment=1.0,
                              input_current_reset=0.0,
                              starting_input_current=0.0,
                              starting_calcium=0.0,                              
                              reset_input_current=True,
                              input_balance=input_balance)

@dataclass
class SynapseTypeParameters:
    stdp_scalar: float
    reward_scalar: float
    max_strength: float
    min_strength: float
    s_tag_decay_rate: float
    starting_s_tag: float
    noise_factor: float

def stdp_synapse_type_parameters():
    return SynapseTypeParameters(stdp_scalar=0.001,
                                 reward_scalar=0.1,
                                 max_strength=0.4,
                                 min_strength=0.0,
                                 s_tag_decay_rate=0.002,
                                 starting_s_tag=0.0,
                                 noise_factor=0.0)

@dataclass
class ModelParameters:
    step_size: int
    starting_dopamine: float
    dopamine_decay: float
    cell_type_parameters: CellTypeParameters
    synapse_type_parameters: SynapseTypeParameters
    
    def __post_init__(self):
        '''
        Used to easily construct object from an exported dict.
        '''
        if isinstance(self.cell_type_parameters, dict):
            self.cell_type_parameters = CellTypeParameters(**self.cell_type_parameters)
        if isinstance(self.synapse_type_parameters, dict):
            self.synapse_type_parameters = SynapseTypeParameters(**self.synapse_type_parameters)

def stdp_model_parameters(input_balance):
    return ModelParameters(step_size=1,
                           starting_dopamine=1.0,
                           dopamine_decay=0.0,
                           cell_type_parameters=stdp_cell_type_parameters(input_balance),
                           synapse_type_parameters=stdp_synapse_type_parameters())

def handwriting_model_parameters(input_balance):
    synapse_type_paramenters = stdp_synapse_type_parameters()
    synapse_type_paramenters.noise_factor = 0.7
    return ModelParameters(step_size=1,
                           starting_dopamine=0.0,
                           dopamine_decay=0.1,
                           cell_type_parameters=stdp_cell_type_parameters(input_balance),
                           synapse_type_parameters=synapse_type_paramenters)

    
# voltage and current should be named potential everywhere
# should probably derive from a "potential generating" class or something
class Synapse:
    def __init__(self, pre_cell, post_cell,
                 synapse_definition, step_size,
                 synapse_type_parameters):
        self.pre_cell = pre_cell
        self.post_cell = post_cell
        self.strength = synapse_definition.starting_strength

        self._step_size = step_size

        # can be though of as recording the firing pattern correlation
        self._s_tag = synapse_type_parameters.starting_s_tag
        
        self._stdp_scalar = synapse_type_parameters.stdp_scalar
        self._reward_scalar = synapse_type_parameters.reward_scalar
        self._max_strength = synapse_type_parameters.max_strength
        self._min_strength = synapse_type_parameters.min_strength
        self._s_tag_decay_rate = synapse_type_parameters.s_tag_decay_rate
        self._noise_factor = synapse_type_parameters.noise_factor

    def update(self, dopamine):
        self.stdp()
        self.train(dopamine)

    def train(self, dopamine):
        self.strength += self._s_tag * dopamine * self._reward_scalar
        if self.strength >= self._max_strength:
            self.strength = self._max_strength
        if self.strength < self._min_strength:
            self.strength = self._min_strength
            
    def stdp(self):
        self._s_tag = decay(self._s_tag, self._s_tag_decay_rate, self._step_size)
        if self.pre_cell.fired():
            self._s_tag -= self._stdp_scalar * self.post_cell.calcium()
        if self.post_cell.fired():
            self._s_tag += self._stdp_scalar * self.pre_cell.calcium()

    def fire(self):
        if self._noise_factor > 0:
            noise = self._noise_factor * random.uniform(-1, 1) * self.strength
            self.post_cell.receive_fire(self.strength + noise)
        else:
            self.post_cell.receive_fire(self.strength)

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
    def __init__(self, cell_definition, cell_membrane, input_balance):
        self.uuid = cell_definition.uuid
        self.label = cell_definition.label
        self._layer_id = cell_definition.layer_id
        self._cell_number = cell_definition.cell_number
        self.x_grid_position = cell_definition.x_grid_position
        self.y_grid_position = cell_definition.y_grid_position
        self._input_balance = input_balance
        self._cell_membrane = cell_membrane

        # I don't like the coupling causing these to be public
        # I don't like how we initialize these outside constructor
        self.input_synapses = []
        self.output_synapses = []
        
        self._initial_total_input_strength = 0.0

    def attach_synapses(self, synapses):
        for synapse in synapses:
            if synapse.pre_cell.uuid == self.uuid:
                self.output_synapses.append(synapse)
            elif synapse.post_cell.uuid == self.uuid:
                self.input_synapses.append(synapse)
            else:
                raise Exception("Attempted to attach synapse to cell but neither of the synapses "\
                                "endpoints attach to the cell.")
        self._initial_total_input_strength = self._current_total_input_strength()

    def apply_input_balance(self):
        if self._input_balance:
            current_total_input_strength = self._current_total_input_strength()
            if current_total_input_strength > 0.0:
                scale_factor = self._initial_total_input_strength / current_total_input_strength
                for synapse in self.input_synapses:
                    synapse.strength = synapse.strength * scale_factor
                
    def _current_total_input_strength(self):
        total = 0.0
        for synapse in self.input_synapses:
            total += synapse.strength
        return total

    def receive_fire(self, strength):
        self._cell_membrane.receive_input(strength)

    def apply_fire(self, step, environment=None):
        if self._cell_membrane.fired():
            for synapse in self.output_synapses:
                synapse.fire()
            if environment is not None:
                environment.accept_fire(step, self.x_grid_position, self.y_grid_position)

    def update(self, step, environment=None):
        if environment is not None:
            outside_current = environment.potential_from_location(step,
                                                                  self.x_grid_position,
                                                                  self.y_grid_position)
            self._cell_membrane.receive_input(outside_current)
        self._cell_membrane.update()
        
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


class SimpleModel:
    def __init__(self, network_definition, model_parameters):
        self.name = "Simple Model"
        self.network_definition = network_definition
        self.model_parameters = model_parameters
        self._dopamine = model_parameters.starting_dopamine
        self._dopamine_decay = model_parameters.dopamine_decay
        self._step_size = model_parameters.step_size
        self._cells, self.synapses = self._build_network(model_parameters.cell_type_parameters,
                                                        model_parameters.synapse_type_parameters,
                                                        network_definition,
                                                        self._step_size)
    def step(self, step, environment=None):
        for cell in self._cells:
            cell.update(step, environment)

        self.update_dopamine(step, environment)

        for synapse in self.synapses:
            synapse.update(self._dopamine)

        for cell in self._cells:
            cell.apply_input_balance()
            cell.apply_fire(step, environment)

    def update_dopamine(self, step, environment=None):
        self._dopamine = decay(self._dopamine, self._dopamine_decay, self._step_size)
        if environment is not None:
            if environment.has_reward() and self._dopamine < 0.1:
                self._dopamine = 1

    def export(self):
        updated_synapse_definitions = []
        for synapse in self.synapses:
            definition = SynapseDefinition(synapse.pre_cell.uuid,
                                                   synapse.post_cell.uuid,
                                                   synapse.strength)
            updated_synapse_definitions.append(definition)
        
        updated_network_definition = NetworkDefinition(
            self.network_definition.cell_definitions,
            updated_synapse_definitions,
            self.network_definition.last_layer_x_grid_position)
                                                               
        blob = {"model_parameters": asdict(self.model_parameters),
                "network_definition": asdict(updated_network_definition),
                "version": "1"
                }
        return blob

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
            cell = Cell(cell_definition, cell_membrane, cell_type_parameters.input_balance)
            cells_by_id[cell.uuid] = cell
            cells.append(cell)

        synapses = []
        synapses_by_cell_id = defaultdict(list)
        for synapse_definition in network_definition.synapse_definitions:
            pre_cell = cells_by_id[synapse_definition.pre_cell_id]
            post_cell = cells_by_id[synapse_definition.post_cell_id]
            synapse = Synapse(pre_cell, post_cell,
                              synapse_definition,
                              step_size,
                              synapse_type_parameters)
            synapses.append(synapse)
            synapses_by_cell_id[synapse_definition.pre_cell_id].append(synapse)
            synapses_by_cell_id[synapse_definition.post_cell_id].append(synapse)

        for cell_id, cell_synapses in synapses_by_cell_id.items():
            cell = cells_by_id[cell_id]
            cell.attach_synapses(cell_synapses)

        return cells, synapses

def import_model(blob):
    network_definition = NetworkDefinition(**blob["network_definition"])
    model_parameters = ModelParameters(**blob["model_parameters"])
    return SimpleModel(network_definition, model_parameters)
