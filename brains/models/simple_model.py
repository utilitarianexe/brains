from brains.utils import decay
from brains.network import SynapseDefinition, NetworkDefinition, CellType

from collections import defaultdict
from dataclasses import dataclass, asdict, field
import random
import numpy as np

@dataclass
class CellTypeParameters:
    voltage_decay: float = 0.01
    current_decay: float = 0.03
    calcium_decay: float = 0.1
    starting_membrane_voltage: float =0.0
    max_voltage: float = 1.0
    voltage_reset: float = -1.0
    calcium_increment: float = 1.0
    input_current_reset: float = 0.0
    starting_calcium: float = 0.0
    starting_input_current: float = 0.0
    reset_input_current: bool = True

@dataclass
class SynapseTypeParameters:
    stdp_scalar: float = 0.01
    reward_scalar: float = 0.1
    max_strength: float = 0.4
    min_strength: float = 0.0
    s_tag_decay_rate: float = 0.002
    starting_s_tag: float = 0.0
    noise_factor: float = 0.0

@dataclass
class ModelParameters:
    step_size: int = 1
    starting_dopamine: float = 1.0
    dopamine_decay: float = 0.0
    cell_type_parameters: CellTypeParameters = field(default_factory=CellTypeParameters)
    synapse_type_parameters: SynapseTypeParameters = field(default_factory=SynapseTypeParameters)
    warp: bool = True
    epoch_length: int = 400
    epoch_delay: int = 50
    
    def __post_init__(self):
        '''
        Used to easily construct object from an exported dict.
        '''
        if isinstance(self.cell_type_parameters, dict):
            self.cell_type_parameters = CellTypeParameters(**self.cell_type_parameters)
        if isinstance(self.synapse_type_parameters, dict):
            self.synapse_type_parameters = SynapseTypeParameters(**self.synapse_type_parameters)


def handwriting_model_parameters(warp=True,
                                 epoch_length=400,
                                 epoch_delay=50):
    synapse_type_paramenters = SynapseTypeParameters(noise_factor=0.5)
    return ModelParameters(starting_dopamine=0.0,
                           dopamine_decay=0.1,
                           synapse_type_parameters=synapse_type_paramenters,
                           warp=warp,
                           epoch_length=epoch_length,
                           epoch_delay=epoch_delay)

    
# voltage and current should be named potential everywhere
# should probably derive from a "potential generating" class or something
class Synapse:
    def __init__(self, pre_cell, post_cell,
                 synapse_definition, step_size,
                 synapse_type_parameters):
        self.pre_cell = pre_cell
        self._cell_type = pre_cell.cell_type
        self.post_cell = post_cell
        self.strength = synapse_definition.starting_strength
        self.label = synapse_definition.label
        self._step_size = step_size

        # can be though of as recording the firing pattern correlation
        self._s_tag = synapse_type_parameters.starting_s_tag
        
        self._stdp_scalar = synapse_type_parameters.stdp_scalar
        self._reward_scalar = synapse_type_parameters.reward_scalar
        self._max_strength = synapse_type_parameters.max_strength
        self._min_strength = synapse_type_parameters.min_strength
        self._s_tag_decay_rate = synapse_type_parameters.s_tag_decay_rate
        self._noise_factor = synapse_type_parameters.noise_factor
        self._pre_cell_fired = False
        self._post_cell_fired = False
        self._last_fire_step = 0

    def update(self, dopamine):
        self.strength += self._s_tag * dopamine * self._reward_scalar
        if self.strength >= self._max_strength:
            self.strength = self._max_strength
        if self.strength < self._min_strength:
            self.strength = self._min_strength

    def post_fire(self, step):
        if self._cell_type == CellType.INHIBITORY:
            return

        steps_sense_last_fire =  step - self._last_fire_step
        self._last_fire_step = step
        self._s_tag = self._s_tag * (1 - self._s_tag_decay_rate)**steps_sense_last_fire
        self._s_tag += self._stdp_scalar * self.pre_cell.calcium()

    def pre_fire(self, step):
        if self._cell_type == CellType.EXCITATORY:
            self._s_tag -= self._stdp_scalar * self.post_cell.calcium()
            steps_sense_last_fire =  step - self._last_fire_step
            self._last_fire_step = step
            self._s_tag = self._s_tag * (1 - self._s_tag_decay_rate)**steps_sense_last_fire

            if self._noise_factor > 0:
                noise = self._noise_factor * random.uniform(-1, 1) * self.strength
                self.post_cell.receive_fire(self.strength + noise)
            else:
                self.post_cell.receive_fire(self.strength)
        elif self._cell_type == CellType.INHIBITORY:
            self.post_cell.receive_fire(self.strength * -1.0)

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
        self.active = True
        self.real_active = True
        self.active_timer = 0

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

    def warp(self, time_steps):
        self.active = True
        self._voltage = self._voltage * (1 - self._voltage_decay)**time_steps
        
        # Figure out integral. 
        # self._voltage += self._input_current * time_steps
        self._input_current = self._input_current * (1 - self._current_decay)**time_steps
        self._calcium = self._calcium * (1 - self._calcium_decay)**time_steps

    def update(self):
        '''
           Voltage and input tend to 0 from both the negative and positive side.
           Changing by higher absalute values the further from 0 they are.

           If voltage gets above one the cell fires and is set to -1
           Input never resets. It just gets added to or decays.

           Calcium increases after firing as a sort of history of recent firing.
        '''
        self._fired = False

        voltage_before_update = self._voltage

        if self._voltage > self._max_voltage:
            self._voltage = self._voltage_reset
            self._fired = True
            self._calcium += self._calcium_increment
            if self._reset_input_current:
                self._input_current = self._input_current_reset

        self._voltage = self._voltage * (1 - self._voltage_decay)**self._step_size
        self._voltage += self._input_current * self._step_size
        self._input_current = self._input_current * (1 - self._current_decay)**self._step_size
        self._calcium = self._calcium * (1 - self._calcium_decay)**self._step_size

        if self._voltage <= 0 or voltage_before_update >= self._voltage:
            self.active = False
        else:
            self.active = True


class Cell:
    def __init__(self, cell_definition, cell_membrane):
        self.uuid = cell_definition.uuid
        self.label = cell_definition.label
        self._layer_id = cell_definition.layer_id
        self._cell_number = cell_definition.cell_number
        self.x_grid_position = cell_definition.x_grid_position
        self.y_grid_position = cell_definition.y_grid_position
        
        self._cell_membrane = cell_membrane
        self.cell_type = cell_definition.cell_type

        # I don't like the coupling causing these to be public
        # I don't like how we initialize these outside constructor
        self.input_synapses = []
        self.output_synapses = []
        self._positive_total_input_strength = 0.0
        self._negative_total_input_strength = 0.0
        self._fire_history = []

        self._target_fire_rate_per_epoch = cell_definition.target_fire_rate_per_epoch
        self._input_balance = cell_definition.input_balance
        self._fire_rate_balance_scalar = 0.01
        self._fire_history_length = 20

    def attach_synapses(self, synapses):
        for synapse in synapses:
            if synapse.pre_cell.uuid == self.uuid:
                self.output_synapses.append(synapse)
            elif synapse.post_cell.uuid == self.uuid:
                self.input_synapses.append(synapse)
            else:
                raise Exception("Attempted to attach synapse to cell but neither of the synapses "\
                                "endpoints attach to the cell.")
        self._positive_total_input_strength = self._current_total_input_strength(CellType.EXCITATORY)
        self._negative_total_input_strength = self._current_total_input_strength(CellType.INHIBITORY)

    def apply_input_balance(self, cell_type):
        current_total_input_strength = self._current_total_input_strength(cell_type)
        if current_total_input_strength > 0.0:
            if cell_type == CellType.EXCITATORY:
                scale_factor = self._positive_total_input_strength / current_total_input_strength
            else:
                scale_factor = self._negative_total_input_strength / current_total_input_strength
            for synapse in self.input_synapses:
                if synapse._cell_type  == cell_type:
                    synapse.strength = synapse.strength * scale_factor

    def fire_rate_balance(self, step, epoch_length):
        if not self._input_balance:
            return

        target_fire_rate = self._target_fire_rate_per_epoch / epoch_length

        if target_fire_rate == 0:
            raise Exception("target fire rate should be greater than 0 with input balancing")
            
        if step == 0:
            return

        new_fire_history = []
        fires = 0
        for fire_time in self._fire_history:
            if fire_time > step  - (epoch_length * self._fire_history_length):
                new_fire_history.append(fire_time)
                fires += 1

        if step > epoch_length * self._fire_history_length:
            running_fire_rate = fires / (epoch_length * self._fire_history_length)
        else:
            running_fire_rate = fires / step
            
        self._fire_history = new_fire_history

        # Print information for one cell in the middle layer and one cell in the output layer.
        if (self._layer_id == 'b' or self._layer_id == 'c') and self._cell_number == 0:
            print(f"xcor {self.x_grid_position} running rate {running_fire_rate} " \
                  f"target rate {target_fire_rate} fires {fires} "\
                  f"total positive in {self._positive_total_input_strength}")

        if running_fire_rate > target_fire_rate:
            down = target_fire_rate/running_fire_rate
            self._positive_total_input_strength -= self._fire_rate_balance_scalar*(self._positive_total_input_strength - self._positive_total_input_strength * down)
            self._negative_total_input_strength -= self._fire_rate_balance_scalar*(self._negative_total_input_strength - self._negative_total_input_strength * down)
        else:
            if running_fire_rate == 0:
                up = 2.0
            else:
                up = target_fire_rate/running_fire_rate
            self._positive_total_input_strength += (self._positive_total_input_strength * up - self._positive_total_input_strength) * self._fire_rate_balance_scalar
            self._negative_total_input_strength += (self._negative_total_input_strength * up - self._negative_total_input_strength) * self._fire_rate_balance_scalar

        self.apply_input_balance(CellType.EXCITATORY)
        self.apply_input_balance(CellType.INHIBITORY)
                
    def _current_total_input_strength(self, cell_type):
        total = 0.0
        for synapse in self.input_synapses:
            if synapse._cell_type == cell_type:
                total += synapse.strength
        return total

    def receive_fire(self, strength):
        self._cell_membrane.receive_input(strength)

    def apply_fire(self, step, environment=None):
        self._fire_history.append(step)
        for synapse in self.output_synapses:
            synapse.pre_fire(step)
        for synapse in self.input_synapses:
            synapse.post_fire(step)
        if environment is not None:
            environment.accept_fire(step, self.x_grid_position, self.y_grid_position)

    def warp(self, time_steps):
        self._cell_membrane.warp(time_steps)

    def update(self, step, environment=None):
        if environment is not None:
            outside_current = environment.potential_from_location(step,
                                                                  self.x_grid_position,
                                                                  self.y_grid_position)
            self._cell_membrane.receive_input(outside_current)
        self._cell_membrane.update()

    def active(self):
        return self._cell_membrane.active
        
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
        self._warp = model_parameters.warp
        self._warping = False
        self._last_active = 0

        self.epoch_length = model_parameters.epoch_length
        self._epoch_delay = model_parameters.epoch_delay

    def _maybe_start_warp(self, step, environment):
        if not self._warp:
            return
        
        active = False
        for cell in self._cells:
            if cell.active():
                active = True
                break
                    
        if self._dopamine > 0.0001:
            active = True

        if environment is not None:
            if environment.active(step):
                active = True

        if not active:
            self._warp_timer += 1
        else:
            self._warp_timer = 0
            
        if self._warp_timer >= 10:
            self._warping = True
            self._warp_timer = 0

    def _epoch_updates(self, step):
        # bad hack(means messing with input delays breaks things
        for synapse in self.synapses:
            synapse._s_tag = 0.0

        for cell in self._cells:
            cell.fire_rate_balance(step, self.epoch_length)
        
    def step(self, step, environment=None):
        self.update_dopamine(step, environment)

        # We need a seperate epoch variable for the model
        real_step = step - self._epoch_delay
        if real_step % self.epoch_length == 0:
            self._epoch_updates(step)

        if self._warping:
            if not environment.active(step) and self._dopamine <= 0.0001:
                return
            for cell in self._cells:
                cell.warp(step - self._last_active)
            self._warping = False
        else:
            self._maybe_start_warp(step, environment)
            if self._warping:
                return
            
        if self._dopamine > 0.0001:
            for synapse in self.synapses:
                synapse.update(self._dopamine)
        
        self._last_active = step
        for cell in self._cells:
            cell.update(step, environment)

        for cell in self._cells:
            if cell.fired():
                cell.apply_fire(step, environment)

    def update_dopamine(self, step, environment=None):
        self._dopamine = decay(self._dopamine, self._dopamine_decay, self._step_size)
        if environment is not None:
            if environment.has_reward():
                self._dopamine = 1

    def export(self):
        updated_synapse_definitions = []
        for synapse in self.synapses:
            definition = SynapseDefinition(synapse.pre_cell.uuid,
                                           synapse.post_cell.uuid,
                                           synapse.strength,
                                           synapse.label)
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

    def _build_network(self, cell_type_parameters,
                       synapse_type_parameters,
                       network_definition,
                       step_size):
        cells_by_id = {}
        cells = []
        for cell_definition in network_definition.cell_definitions:
            cell_membrane = CellMembrane(cell_type_parameters, step_size)
            cell = Cell(cell_definition, cell_membrane)
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

def import_model(blob, warp=True):
    network_definition = NetworkDefinition(**blob["network_definition"])
    model_parameters = ModelParameters(**blob["model_parameters"])
    model_parameters.warp = warp
    return SimpleModel(network_definition, model_parameters)
