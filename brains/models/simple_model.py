from brains.utils import decay
from brains.network import SynapseDefinition, NetworkDefinition, CellType
import iron_brains

from collections import defaultdict
import random
import dataclasses

class Synapse:
    def __init__(self, pre_cell, post_cell,
                 synapse_definition, step_size,
                 synapse_type_parameters, iron_model):

        self._iron_model = iron_model
        self._index = iron_brains.add_synapse(self._iron_model,
                                              synapse_definition.unsupervised_stdp,
                                              synapse_definition.starting_strength,
                                              synapse_definition.starting_inhibitory_strength)
                                              
        
        self.pre_cell = pre_cell
        self._pre_cell_type = pre_cell.cell_type
        self.post_cell = post_cell
        self.label = synapse_definition.label
        
        # self._reward_scalar = synapse_definition.reward_scalar
        # self._s_tag_decay_rate = synapse_definition.s_tag_decay_rate
        # self._max_strength = synapse_type_parameters.max_strength
        # self._min_strength = synapse_type_parameters.min_strength
        
        # self._step_size = step_size
        
        self._noise_factor = synapse_type_parameters.noise_factor
        self._stdp_scalar = synapse_type_parameters.stdp_scalar
        

        # self._unsupervised_stdp = synapse_definition.unsupervised_stdp
        # self.strength = synapse_definition.starting_strength
        # self.inhibitory_strength = synapse_definition.starting_inhibitory_strength
        # self._s_tag = synapse_type_parameters.starting_s_tag

        self._pre_cell_fired = False
        self._post_cell_fired = False

        #self._last_s_tag_decay = 0

    @property
    def s_tag(self):
        return iron_brains.s_tag(self._iron_model, self._index)

    @s_tag.setter
    def s_tag(self, value):
        iron_brains.update_s_tag(self._iron_model, self._index, value)


    @property
    def strength(self):
        return iron_brains.strength(self._iron_model, self._index)

    @strength.setter
    def strength(self, value):
        iron_brains.update_strength(self._iron_model, self._index, value)

    @property
    def inhibitory_strength(self):
        return iron_brains.inhibitory_strength(self._iron_model, self._index)

    @inhibitory_strength.setter
    def inhibitory_strength(self, value):
        iron_brains.update_inhibitory_strength(self._iron_model, self._index, value)


    # def update(self, step, dopamine):
    #     self._decay_s_tag(step)
    #     if self._unsupervised_stdp:
    #         self.strength += self._s_tag * self._reward_scalar
    #     else:
    #         self.strength += self._s_tag * dopamine * self._reward_scalar
    #     self.cap()


    def cap(self):
        iron_brains.cap(self._iron_model, self._index)
        # if self.strength >= self._max_strength:
        #     self.strength = self._max_strength
        
        # if self.strength < self._min_strength:
        #     self.strength = self._min_strength

        # if self.inhibitory_strength >= self._max_strength:
        #     self.inhibitory_strength = self._max_strength
            
        # if self.inhibitory_strength < self._min_strength:
        #     self.inhibitory_strength = self._min_strength

    # def _decay_s_tag(self, step):
    #     steps_sense_last_s_tag_decay=  step - self._last_s_tag_decay
    #     self._last_s_tag_decay = step
    #     self._s_tag = self._s_tag * (1 - self._s_tag_decay_rate)**steps_sense_last_s_tag_decay


    def post_fire(self, step):
        if self._pre_cell_type == CellType.INHIBITORY:
            return

        # self._decay_s_tag(step)
        self.s_tag += self._stdp_scalar * self.pre_cell.calcium()

    def pre_fire(self, step):
        if self._pre_cell_type == CellType.INHIBITORY or self._pre_cell_type == CellType.MIXED:
            self.post_cell.receive_fire(self.inhibitory_strength * -1.0)

        if self._pre_cell_type == CellType.EXCITATORY or self._pre_cell_type == CellType.MIXED:
            # self._decay_s_tag(step)
            self.s_tag -= self._stdp_scalar * self.post_cell.calcium()

            if self._noise_factor > 0:
                noise = self._noise_factor * random.uniform(-1, 1) * self.strength
                self.post_cell.receive_fire(self.strength + noise)
            else:
                self.post_cell.receive_fire(self.strength)

class CellMembrane:
    def __init__(self, iron_model, index):
        self.iron_model = iron_model
        self.index = index

    def voltage(self):
        return iron_brains.voltage(self.iron_model, self.index)

    def calcium(self):
        return iron_brains.calcium(self.iron_model, self.index)

    def fired(self):
        return iron_brains.fired(self.iron_model, self.index)
        
    def receive_input(self, strength):
        iron_brains.receive_input(self.iron_model, self.index, strength)

    

class Cell:
    def __init__(self, cell_definition, cell_membrane):
        self.uuid = cell_definition.uuid
        self.label = cell_definition.label
        self.layer_id = cell_definition.layer_id
        
        self.x_display_position = cell_definition.x_display_position
        self.y_display_position = cell_definition.y_display_position
        self.x_layer_position = cell_definition.x_layer_position
        self.y_layer_position = cell_definition.y_layer_position
        self._is_input_cell = cell_definition.is_input_cell
        self._x_input_position = cell_definition.x_input_position
        self._y_input_position = cell_definition.y_input_position
        self.is_output_cell = cell_definition.is_output_cell
        self.output_id = cell_definition.output_id
        
        self._cell_membrane = cell_membrane
        self.cell_type = cell_definition.cell_type
        self.fire_trace = 0

        # I don't like the coupling causing these to be public
        # I don't like how we initialize these outside constructor
        self.input_synapses = []
        self.output_synapses = []
        self._target_input = 0.0
        
        self._fire_history = []
        self._target_fire_rate_per_epoch = cell_definition.target_fire_rate_per_epoch
        self._input_balance = cell_definition.input_balance
        self._output_balance = cell_definition.output_balance
        self._lock_inhibition_strength = cell_definition.lock_inhibition_strength
        
        self._fire_rate_balance_scalar = 0.01
        self._fire_history_length = 20
        self._input_balance_scalar = 1.0

    def weight_totals(self):
        (positive_in, negative_in, positive_out, negative_out,) = (0.0, 0.0, 0.0, 0.0,)
        for synapse in self.input_synapses:
            positive_in += synapse.strength
            negative_in += synapse.inhibitory_strength
        for synapse in self.output_synapses:
            positive_out += synapse.strength
            negative_out += synapse.inhibitory_strength
        return positive_in, negative_in, positive_out, negative_out

    def attach_synapses(self, synapses):
        for synapse in synapses:
            if synapse.pre_cell.uuid == self.uuid:
                self.output_synapses.append(synapse)
            elif synapse.post_cell.uuid == self.uuid:
                self.input_synapses.append(synapse)
            else:
                raise Exception("Attempted to attach synapse to cell "\
                                "but neither of the synapses "\
                                "endpoints attach to the cell.")
        current_positive_strength = self._positive_input_strength()
        self._target_input = current_positive_strength

    def _apply_negative_input_balance(self, target_negative_input_strength,):
        current_negative_strength = self._negative_input_strength()
        if current_negative_strength > 0.0:
            negative_scale_factor = target_negative_input_strength/current_negative_strength
        else:
            negative_scale_factor = 1.0
            
        real_negative_input_strength = 0.0
        change_factor = negative_scale_factor * self._input_balance_scalar
        keep_factor = 1 - self._input_balance_scalar
        for synapse in self.input_synapses:
            change_part = synapse.inhibitory_strength * change_factor
            synapse.inhibitory_strength = (change_part) + (synapse.inhibitory_strength * keep_factor)
            synapse.cap()
            real_negative_input_strength += synapse.inhibitory_strength
        return real_negative_input_strength

    def _apply_positive_input_balance(self, target_positive_input_strength,):
        current_positive_strength = self._positive_input_strength()
        if current_positive_strength > 0.0:
            positive_scale_factor = target_positive_input_strength / current_positive_strength
        else:
            positive_scale_factor = 1.0

        real_positive_input_strength = 0.0
        change_factor = positive_scale_factor * self._input_balance_scalar
        keep_factor = 1 - self._input_balance_scalar
        for synapse in self.input_synapses:
            # bunch of bullshit for performance
            strength = iron_brains.strength(synapse._iron_model, synapse._index)
            new_strength = (strength * change_factor) + (strength * keep_factor)
            iron_brains.update_strength(synapse._iron_model, synapse._index, new_strength)
            synapse.cap()
            if not self._lock_inhibition_strength:
                real_positive_input_strength += iron_brains.strength(synapse._iron_model,
                                                                     synapse._index)
        # more performance bs
        if self._lock_inhibition_strength:
            return real_positive_input_strength
        else:
            return 1.0

    def output_balance(self):
        if not self._output_balance:
            return

        if len(self.output_synapses) == 0:
            return

        if self.cell_type == CellType.EXCITATORY or self.cell_type == CellType.MIXED:
            total_post_cell_strength = 0.0
            num_cells = 0
            for synapse in self.output_synapses:
                total_post_cell_strength += synapse.post_cell._target_input
                if synapse.post_cell._target_input > 0:
                    num_cells += 1

            if num_cells > 0:
                average_post_cell_strength = total_post_cell_strength/num_cells
                if self._positive_output_strenght() == 0:
                    reset = average_post_cell_strength/len(self.output_synapses)
                    for synapse in self.output_synapses:
                        synapse.strength = reset
                else:
                    scale = average_post_cell_strength/self._positive_output_strenght()
                    for synapse in self.output_synapses:
                        synapse.strength = synapse.strength * scale

        if self.cell_type == CellType.INHIBITORY or self.cell_type == CellType.MIXED:
            if self._lock_inhibition_strength:
                return
            n_total_post_cell_strength = 0.0
            num_cells = 0
            for synapse in self.output_synapses:
                n_total_post_cell_strength += synapse.post_cell._target_input
                if synapse.post_cell._target_input > 0:
                    num_cells += 1

            if num_cells > 0:
                n_average_post_cell_strength = n_total_post_cell_strength/num_cells
                n_scale = n_average_post_cell_strength/self._negative_output_strength()
                for synapse in self.output_synapses:
                    synapse.inhibitory_strength = synapse.inhibitory_strength * n_scale

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

        if running_fire_rate > target_fire_rate:
            rate_based_down_scale_factor = target_fire_rate/running_fire_rate
            self._target_input -= self._target_strength_reduction(
                rate_based_down_scale_factor,
                self._target_input)
        else:
            if running_fire_rate == 0:
                rate_based_up_scale_factor = 2.0
            else:
                rate_based_up_scale_factor = target_fire_rate/running_fire_rate

            self._target_input += self._target_strength_increase(rate_based_up_scale_factor,
                                                     self._target_input)

        real_positive_strength = self._apply_positive_input_balance(self._target_input)

        if not self._lock_inhibition_strength:
            real_negative_strength = self._apply_negative_input_balance(self._target_input)
        else:
            real_negative_strength = 0.0
        
        if real_negative_strength == 0.0:
            pass
        elif real_positive_strength < real_negative_strength:
            real_positive_strength = self._apply_positive_input_balance(
                real_positive_strength)
            real_negative_strength = self._apply_negative_input_balance(
                real_positive_strength)

        else:
            real_positive_strength = self._apply_positive_input_balance(
                real_negative_strength)
            real_negative_strength = self._apply_negative_input_balance(
                real_negative_strength)

    def _target_strength_reduction(self, rate_based_down_scale_factor,
                                   current_target_strength):
        rate_based_target = current_target_strength * rate_based_down_scale_factor
        rate_based_change = current_target_strength - rate_based_target
        return self._fire_rate_balance_scalar * rate_based_change
    
    def _target_strength_increase(self, rate_based_up_scale_factor, current_target_strength):
        rate_based_target = current_target_strength * rate_based_up_scale_factor
        rate_based_change = rate_based_target - current_target_strength
        return self._fire_rate_balance_scalar * rate_based_change
                
    def _current_total_input_strength(self):
        positive_total = 0.0
        negative_total = 0.0
        for synapse in self.input_synapses:
            positive_total += synapse.strength
            negative_total += synapse.inhibitory_strength
        return positive_total, negative_total

    def _positive_input_strength(self):
        positive_total = 0.0
        for synapse in self.input_synapses:
            positive_total += iron_brains.strength(synapse._iron_model, synapse._index)
        return positive_total

    def _negative_input_strength(self):
        negative_total = 0.0
        for synapse in self.input_synapses:
            negative_total += synapse.inhibitory_strength
        return negative_total

    def _positive_output_strenght(self):
        total = 0.0
        for synapse in self.output_synapses:
            total += synapse.strength
        return total

    def _negative_output_strength(self):
        total = 0.0
        for synapse in self.output_synapses:
            total += synapse.inhibitory_strength
        return total

    def receive_fire(self, strength):
        self._cell_membrane.receive_input(strength)

    def apply_fire(self, step):
        self._fire_history.append(step)
        for synapse in self.output_synapses:
            synapse.pre_fire(step)

        for synapse in self.input_synapses:
            synapse.post_fire(step)
  
    def active(self):
        return self._cell_membrane.active
        
    def membrane_voltage(self):
        return self._cell_membrane.voltage()

    def calcium(self):
        return self._cell_membrane.calcium()
    
    def fired(self):
        return self._cell_membrane.fired()

    def drawable_synapses(self):
        drawables = []
        for synapse in self.input_synapses:
            if synapse.pre_cell.cell_type == CellType.EXCITATORY:
                strength_text = str(round(synapse.strength, 5))
                drawable = {"text": strength_text,
                            "x": synapse.pre_cell.x_layer_position,
                            "y": synapse.pre_cell.y_layer_position,
                            "matrix_label": "in_excite"}
                drawables.append(drawable)
            elif synapse.pre_cell.cell_type == CellType.INHIBITORY:
                strength_text = str(round(synapse.inhibitory_strength, 5))
                drawable = {"text": strength_text,
                            "x": synapse.pre_cell.x_layer_position,
                            "y": synapse.pre_cell.y_layer_position,
                            "matrix_label": "in_inhibit"}
                drawables.append(drawable)
        for synapse in self.output_synapses:
            strength_text = str(round(synapse.strength, 5))
            drawable = {"text": strength_text,
                        "x": synapse.post_cell.x_layer_position,
                        "y": synapse.post_cell.y_layer_position,
                        "matrix_label": "out_excite"}
            drawables.append(drawable)
            if synapse.inhibitory_strength > 0.0:
                strength_text = str(round(synapse.inhibitory_strength, 5))
                drawable = {"text": strength_text,
                            "x": synapse.post_cell.x_layer_position,
                            "y": synapse.post_cell.y_layer_position,
                            "matrix_label": "out_inhibit"}
                drawables.append(drawable)
        return drawables

class SimpleModel:
    def __init__(self, network_definition, model_parameters):
        self.name = "Simple Model"
        self.network_definition = network_definition
        self.model_parameters = model_parameters
        self._dopamine = model_parameters.starting_dopamine
        self._dopamine_decay = model_parameters.dopamine_decay
        self._step_size = model_parameters.step_size
        self._iron_model = iron_brains.create(len(network_definition.cell_definitions))
        
        self._cells, self.synapses = self._build_network(
            model_parameters.cell_type_parameters,
            model_parameters.synapse_type_parameters,
            network_definition,
            self._step_size)

        self.epoch_length = model_parameters.epoch_length
        self._epoch_delay = model_parameters.epoch_delay

        # misleading name
        self.rewarded_synapses = []
        for synapse in self.synapses:
            if synapse._pre_cell_type != CellType.INHIBITORY:
                self.rewarded_synapses.append(synapse)

        self.cells_by_input_position = self._cells_by_input_position()
        
    def step(self, step, stimuli, has_reward, active_environment):
        self._update_dopamine(step, has_reward)

        # We need a seperate epoch variable for the model
        real_step = step - self._epoch_delay
        if real_step % self.epoch_length == 0:
            self._epoch_updates(step)

        iron_brains.update_synapses(self._iron_model, self._dopamine)
        
        self._apply_stimuli(stimuli)
        iron_brains.update_cells(self._iron_model)

        output_ids = []
        for cell in self._cells:
            if cell.fired():
                cell.fire_trace = 100
                cell.apply_fire(step)
                if cell.is_output_cell:
                    output_ids.append(cell.output_id)
            else:
                if cell.fire_trace > 0:
                    cell.fire_trace -= 1

        return output_ids


    def _cells_by_input_position(self):
        cells_by_input_position = defaultdict(lambda: defaultdict(list))
        for cell in self._cells:
            if cell._is_input_cell:
                cells_by_input_position[cell._x_input_position][cell._y_input_position].append(cell)
        return cells_by_input_position

    def _apply_stimuli(self, stimuli):
        if stimuli is None:
            return
        
        for stimulus in stimuli:
            x_input_position = stimulus[0]
            y_input_position = stimulus[1]
            outside_current = stimulus[2]
            cells = self.cells_by_input_position[x_input_position][y_input_position]
            for cell in cells:
                cell._cell_membrane.receive_input(outside_current)

    def _epoch_updates(self, step):
        # bad hack(means messing with input delays breaks things
        for synapse in self.synapses:
            synapse.s_tag = 0.0

        for cell in self._cells:
            cell.output_balance()

        for cell in self._cells:
            cell.fire_rate_balance(step, self.epoch_length)

        for cell in self._cells:
            cell.synapses_to_update = {}

    def _update_dopamine(self, step, has_reward):
        self._dopamine = decay(self._dopamine, self._dopamine_decay, self._step_size)
        if has_reward:
            self._dopamine = 1

    def export(self):
        updated_synapse_definitions = []
        for synapse in self.synapses:
            definition = SynapseDefinition(
                synapse.label,
                synapse.pre_cell.uuid,
                synapse.post_cell.uuid,
                synapse.strength,
                synapse.inhibitory_strength)
            updated_synapse_definitions.append(definition)
        
        updated_network_definition = NetworkDefinition(
            self.network_definition.cell_definitions,
            updated_synapse_definitions)
                                                               
        blob = {"model_parameters": dataclasses.asdict(self.model_parameters),
                "network_definition": dataclasses.asdict(updated_network_definition),
                "version": "1"
                }
        return blob

    def video_output(self, x, y, layer):
        '''
        Used by pygame
        '''
        texts = ["dopamine: " + str(round(self._dopamine, 5))]
        drawables = []
        for cell in self._cells:
            spike = cell.fire_trace > 0
            drawable = {"x": cell.x_display_position,
                        "y": cell.y_display_position,
                        "strength": cell.membrane_voltage(),
                        "spike": spike,
                        "layer_id": cell.layer_id,
                        "layer_x": cell.x_layer_position,
                        "layer_y": cell.y_layer_position}
            drawables.append(drawable)
            wanted_position = cell.x_layer_position == x and cell.y_layer_position == y
            wanted_layer = cell.layer_id == layer
            if wanted_position and wanted_layer:
                totals = cell.weight_totals()
                (positive_in, negative_in, positive_out, negative_out,) = totals
                texts.append(f"positive_in: {str(round(positive_in, 5))} "\
                             f"negative_in: {str(round(negative_in, 5))} "\
                             f"positive_out: {str(round(positive_out, 5))} "\
                             f"negative_out: {str(round(negative_out, 5))} "\
                             f"target: {str(round(cell._target_input, 5))} ")
                drawables += cell.drawable_synapses()
        return drawables, texts

    def text_output(self):
        '''
        Used for command line prints once an epoch
        '''
        texts = []
        for cell in self._cells:
            # Print information for one cell in the middle layer and one cell in the output layer.
            if (cell.layer_id == 'b' or cell.layer_id == 'c') and cell.output_id == 0:
                texts.append(f"layer_id {cell.layer_id} " \
                    f"running_rate {len(cell._fire_history) / cell._fire_history_length} " \
                    f"target_rate {cell._target_fire_rate_per_epoch} " \
                    f"fires {len(cell._fire_history)} " \
                    f"target_input {cell._target_input}")
        return texts

    def test_outputs(self):
        outputs = {}
        for cell in self._cells:
            outputs[cell.label] = cell.membrane_voltage()

        for synapse in self.synapses:
            label = f"{synapse.pre_cell.label}_to_{synapse.post_cell.label}"
            outputs[label] = synapse.strength
        return outputs

    def outputs(self):
        '''
        Used by pyplot
        '''
        total_negative_in = 0.0
        total_positive_in = 0.0
        total_negative_out = 0.0
        total_positive_out = 0.0
        cell_to_print = None
        for cell in self._cells:
            correct_position = cell.x_layer_position == 0 and cell.y_layer_position == 0
            if cell.layer_id == 'b' and correct_position:
                cell_to_print = cell
                break
        if cell_to_print is None:
            return {}

        for synapse in cell_to_print.input_synapses:
            total_positive_in += synapse.strength
            total_negative_in += synapse.inhibitory_strength

        for synapse in cell_to_print.output_synapses:
            total_positive_out += synapse.strength
            total_negative_out += synapse.inhibitory_strength
        return {"positive_in": total_positive_in,
                "negative_in": total_negative_in,
                "positive_out": total_positive_out,
                "negative_out": total_negative_out,}

    def _build_network(self, cell_type_parameters,
                       synapse_type_parameters,
                       network_definition,
                       step_size):
        cells_by_id = {}
        cells = []
        for i, cell_definition in enumerate(network_definition.cell_definitions):
            cell_membrane = CellMembrane(self._iron_model, i)
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
                              synapse_type_parameters, self._iron_model)
            synapses.append(synapse)
            synapses_by_cell_id[synapse_definition.pre_cell_id].append(synapse)
            synapses_by_cell_id[synapse_definition.post_cell_id].append(synapse)

        for cell_id, cell_synapses in synapses_by_cell_id.items():
            cell = cells_by_id[cell_id]
            cell.attach_synapses(cell_synapses)

        return cells, synapses
