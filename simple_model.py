import collections
from dataclasses import dataclass

@dataclass
class CellTypeParameters:
    voltage_decay: float
    current_decay: float
    calcium_decay: float
    starting_membrane_voltage: float

@dataclass
class SynapseTypeParameters:
    stdp_scalar: float

def decay(initial_value, decay_rate, step_size):
    return initial_value * (1 - decay_rate)**step_size


# voltage and current should be named potential everywhere
# should probably derive from a "potential generating" class or something
# fix tests
class Synapse:
    def __init__(self, starting_strength, stdp_scalar, pre_cell, post_cell):
        # much of this could be private
        self.strength = starting_strength
        self.pre_cell = pre_cell
        self.post_cell = post_cell
        self.stdp_scalar = stdp_scalar

        # can be though of as recording the firing pattern correlation
        self.s_tag = 0

    def update(self, dopamine):
        self.stdp()
        self.train(dopamine)

    def train(self, dopamine):
        # oh god magic
        self.strength += self.s_tag * dopamine * 0.1
        if self.strength >= 0.4:
            self.strength = 0.4
        if self.strength < 0:
            self.strength = 0
            
    def stdp(self):
        # fix step size
        self.s_tag = decay(self.s_tag, 0.003, 1)
        
        if self.pre_cell.fired():
            self.s_tag -= self.stdp_scalar * self.post_cell.cell_membrane.calcium
        if self.post_cell.fired():
            self.s_tag += self.stdp_scalar * self.pre_cell.cell_membrane.calcium

class CellMembrane:
    def __init__(self, voltage_decay, current_decay, calcium_decay,
                 starting_voltage, step_size):
        self._voltage_decay = voltage_decay
        self._current_decay = current_decay
        self._calcium_decay = calcium_decay
        self._voltage = starting_voltage
        
        # need a magic numbe sweep
        # Don't really like that this is public
        self.input_current = 0
        self.calcium = 0
        self._step_size = step_size
        self._fired = False # why not just check voltage
        
    def voltage(self):
        return self._voltage

    def fired(self):
        return self._fired

    # need to think about step sizes
    def update(self):
        '''
           Voltage and input tend to 0 from both the negative and positive side.
           Changing by higher absalute values the further from 0 they are.

           If voltage gets above one the cell fires and is set to -1
           Input never resets. It just gets added to or decays.

           Calcium spikes after firing as a sort of history of recent firing.
        '''
        self._fired = False
        # magic numbers
        if self._voltage > 1:
            # do we need to reset to -1
            self._voltage = -1
            self._fired = True
            self.calcium += 1
            # make optional
            self.input_current = 0

        self._voltage = decay(self._voltage, self._current_decay, self._step_size)
        self._voltage += self.input_current * self._step_size
        self.input_current = decay(self.input_current, self._current_decay, self._step_size)
        self.calcium = decay(self.calcium, self._calcium_decay, self._step_size)



class Cell:
    def __init__(self, id, x_grid_position, y_grid_position,
                 cell_membrane, input_synapses, output_synapses,
                 environment):
        self.id = id
        self.x_grid_position = x_grid_position
        self.y_grid_position = y_grid_position
        self._environment = environment
        
        # I don't like the coupling causing these to be public
        self.input_synapses = input_synapses # not acutally used yet
        self.output_synapses = output_synapses
        self.cell_membrane = cell_membrane
        
    def membrane_voltage(self):
        return self.cell_membrane.voltage()

    def fired(self):
        return self.cell_membrane.fired()

    def apply_fire(self):
        if self.cell_membrane.fired():
            for synapse in self.output_synapses:
                # ugly
                synapse.post_cell.cell_membrane.input_current += synapse.strength

    def update(self, step):
        outside_current = self._environment.potential_from_location(step,
                                                                    self.x_grid_position,
                                                                    self.y_grid_position)
        self.cell_membrane.input_current += outside_current
        self.cell_membrane.update()
    
class SimpleModel:
    def __init__(self,  cell_parameters, synapse_parameters,
                 network_definition, environment,
                 starting_dopamine, dopamine_decay,
                 step_size):
        self.name = "Simple Model"
        self._environment = environment
        self._cells, self._synapses = self._build_network(cell_parameters,
                                                          synapse_parameters,
                                                          network_definition,
                                                          step_size)
        self._dopamine = starting_dopamine
        self._dopamine_decay = dopamine_decay
        self._step_size = step_size

    def update_dopamine(self, step):
        self._dopamine = decay(self._dopamine, self._dopamine_decay, self._step_size)
        for cell in self._cells:
            if cell.fired():
                if self._environment.reward(step, cell.id):
                    self._dopamine += 1

    def step(self, step):
        for cell in self._cells:
            cell.update(step)

        for cell in self._cells:
            cell.apply_fire()

        self.update_dopamine(step)

        for synapse in self._synapses:
            synapse.update(self._dopamine)

    def synapse_output(self):

        out_line += "\n"
        return out_line

    def video_output(self):
        drawables = []
        for cell in self._cells:
            # maybe make a class
            drawable = {"id": cell.id,
                        "x": cell.x_grid_position, "y": cell.y_grid_position,
                        "strength": cell.membrane_voltage()}
            drawables.append(drawable)
        texts = ["dopamine: " + str(round(self._dopamine, 4))]
        return (drawables, texts)


    def outputs(self):
        output = {}
        for cell in self._cells:
            output[cell.id] = cell.membrane_voltage()
            if cell.id == 'c':
                output['input'] = cell.cell_membrane.input_current
        for synapse in self._synapses:
            if synapse.pre_cell.id == "a" and synapse.post_cell.id == "c":
                output["a c synapse"] = synapse.strength
            if synapse.pre_cell.id == "b" and synapse.post_cell.id == "c":
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
        for cell_parameters in network_definition.per_cell_parameters:
            id = cell_parameters.id
            cell_membrane = CellMembrane(cell_type_parameters.voltage_decay,
                                         cell_type_parameters.current_decay,
                                         cell_type_parameters.calcium_decay,
                                         cell_type_parameters.starting_membrane_voltage,
                                         step_size)
            cell = Cell(id,
                        cell_parameters.x_grid_position,
                        cell_parameters.y_grid_position,
                        cell_membrane, [], [], self._environment)
            cells_by_id[id] = cell
            cells.append(cell)

        synapses = []
        for synapse_parameters in network_definition.per_synapse_parameters:
            pre_cell = cells_by_id[synapse_parameters.pre_cell_id]
            post_cell = cells_by_id[synapse_parameters.post_cell_id]
            synapse  = Synapse(synapse_parameters.starting_strength,
                               synapse_type_parameters.stdp_scalar,
                               pre_cell, post_cell)
            synapses.append(synapse)
            pre_cell.output_synapses.append(synapse)
            post_cell.input_synapses.append(synapse)

        return cells, synapses
