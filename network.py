from dataclasses import dataclass
import random
from collections import defaultdict
from enum import Enum

# kinda a lot of display stuff in this class
# grid position is very display like

class Layout(Enum):
     SQUARE = 1
     LINE = 2

@dataclass
class PerCellParameters:
    id: str
    x_grid_position: int
    y_grid_position: int

@dataclass
class PerSynapseParameters:
    pre_cell_id: str
    post_cell_id: str
    starting_strength: float

@dataclass
class NetworkDefinition:
    per_cell_parameters: list
    per_synapse_parameters: list
    cell_id_with_fake_input: str

class Layer:
    def __init__(self, id, size, starting_x_position, layout=Layout.LINE):
        self.id = id
        self.size = size
        self.layout = layout
        self.starting_x_position = starting_x_position
        self.edge_length = self._layer_edge_length()

    def _newtons_square_root(n):
        x = n
        y = (x + 1) // 2
        while y < x:
            x = y
            y = (x + n // x) // 2
        return x

    def _layer_edge_length(self):
        if self.layout == Layout.LINE:
            return 1
        
        sqrt = Layer._newtons_square_root(self.size)
        if sqrt**2 == self.size:
            return sqrt
        return sqrt + 1

    def cell_layer_position(self, cell_number):
        if self.layout == Layout.LINE:
            return (0, cell_number,)

        x = cell_number % self.edge_length
        y = cell_number // self.edge_length
        return (x, y,)

    def cell_position(self, cell_number):
        (layer_position_x, layer_position_y, ) = self.cell_layer_position(cell_number)
        return self.starting_x_position + layer_position_x, layer_position_y


# other ways to do this to
@dataclass
class LayerConnection:
    pre_layer: Layer
    post_layer: Layer
    degree: float
    
def build_layer_based_network(layer_definitions, layer_connections, cell_id_with_fake_input):
    layers = layers_from_definitons(layer_definitions)
    synapse_end_points, cell_id_and_grid_positions  = edge_list_from_layers(layers, layer_connections)
    return network_from_edge_list(cell_id_and_grid_positions,
                                  synapse_end_points,
                                  cell_id_with_fake_input)

def layers_from_definitons(layer_definitions):
    layers = []
    starting_x_position = 0
    for layer_definition in layer_definitions:
        (id, size, layout) = layer_definition
        layer = Layer(id, size, starting_x_position, layout)
        layers.append(layer)
        starting_x_position += layer.edge_length + 2
    return layers

# should not be called grid position in this file
def edge_list_from_layers(layers, layer_connections):
    cell_id_and_grid_positions = []
    cell_ids_by_layer = defaultdict(list)
    for layer in layers:
        for cell_number in range(layer.size):
            cell_id = (layer.id, cell_number,)
            grid_position = layer.cell_position(cell_number)
            cell_id_and_grid_positions.append((cell_id, grid_position,))
            cell_ids_by_layer[layer.id].append(cell_id)

    synapse_end_points = []
    for (pre_layer, post_layer, probability, synapse_strength) in layer_connections:
        for cell_id_pre_layer in cell_ids_by_layer[pre_layer]:
            for cell_id_post_layer in cell_ids_by_layer[post_layer]:
                if probability >= random.random():
                    synapse_end_point = (cell_id_pre_layer, cell_id_post_layer, synapse_strength)
                    synapse_end_points.append(synapse_end_point)
    return synapse_end_points, cell_id_and_grid_positions 
                         
# needs test and to validate input
# also not sure if our actual graph data structure is the best way to compute
def network_from_edge_list(cell_id_and_grid_positions,
                           synapse_end_points,
                           cell_id_with_fake_input):
    '''
    Grid position is purely for display
    '''

    # dont like how we are doing plurals
    per_cell_parameters = []
    for (cell_id, (x_grid_pos, y_grid_pos)) in cell_id_and_grid_positions:
        cell_parameters = PerCellParameters(cell_id, x_grid_pos, y_grid_pos)
        per_cell_parameters.append(cell_parameters)

    per_synapse_parameters = []
    for (pre_cell_id, post_cell_id, strength) in synapse_end_points:
        per_synapse_parameters.append(PerSynapseParameters(pre_cell_id, post_cell_id, strength))
        
    return NetworkDefinition(per_cell_parameters,
                             per_synapse_parameters,
                             cell_id_with_fake_input)
