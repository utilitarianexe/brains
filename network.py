from dataclasses import dataclass
import random
from collections import defaultdict
from enum import Enum
from typing import Callable

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
    
def build_layer_based_network(layer_definitions, layer_connections):
    layers = layers_from_definitons(layer_definitions)
    synapse_end_points, per_cell_information = edge_list_from_layers(layers, layer_connections)
    return classes_from_tuples(per_cell_information,
                               synapse_end_points)

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
    per_cell_information = []
    cell_ids_by_layer = defaultdict(list)
    for layer in layers:
        for cell_number in range(layer.size):
            cell_id = (layer.id, cell_number,)
            grid_position = layer.cell_position(cell_number)
            per_cell_information.append((cell_id, grid_position,))
            cell_ids_by_layer[layer.id].append(cell_id)

    synapse_end_points = []
    for (pre_layer, post_layer, probability, synapse_strength) in layer_connections:
        for cell_id_pre_layer in cell_ids_by_layer[pre_layer]:
            for cell_id_post_layer in cell_ids_by_layer[post_layer]:
                if probability >= random.random():
                    synapse_end_point = (cell_id_pre_layer, cell_id_post_layer, synapse_strength)
                    synapse_end_points.append(synapse_end_point)
    return synapse_end_points, per_cell_information
                         

# needs test and to validate input
# also not sure if our actual graph data structure is the best way to compute
# this is just a dumb function
def classes_from_tuples(per_cell_tuple,
                        per_synapse_tuple):
    '''
    This function is just to get us to classes from tuples
    '''

    per_cell_parameters = []
    for (cell_id, (x_grid_pos, y_grid_pos,),) in per_cell_tuple:
        cell_parameters = PerCellParameters(cell_id, x_grid_pos, y_grid_pos)
        per_cell_parameters.append(cell_parameters)

    per_synapse_parameters = []
    for (pre_cell_id, post_cell_id, strength) in  per_synapse_tuple:
        per_synapse_parameters.append(PerSynapseParameters(pre_cell_id, post_cell_id, strength))
        
    return NetworkDefinition(per_cell_parameters,
                             per_synapse_parameters)


# eventually these should take a strength scaler parameter from the model
def small_default_network():
    per_cell_tuple = [("a", (0, 0),),
                      ("b", (1, 0),),
                      ("c", (2, 0),), ("d", (2, 1)),
                      ("e", (3, 0),)]
    per_synapse_tuple = [("a", "b", 0.15),
                         ("b", "c", 0.15),
                         ("b", "d", 0.15),
                         ("c", "e", 0.15),
                         ("d", "e", 0.15),]
    return classes_from_tuples(per_cell_tuple,
                               per_synapse_tuple)

# eventually these should take a strenght modifier parameter from the model
def layer_based_default_network():
    image_size = 28*28
    layers = [("a", image_size, Layout.SQUARE,),
              ("b", 25, Layout.SQUARE,),
              ("c", 25, Layout.SQUARE,),
              ("d", 2, Layout.LINE,)]
    
    # Something about connection probability rubs me wrong.
    # connections might be more complex
    layer_connections = [("a", "b", 1, 0.003), ("b", "c", 1, 0.012),
                         ("c", "d", 1, 0.007)]
    return build_layer_based_network(layers, layer_connections)
