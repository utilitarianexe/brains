import brains.utils as utils

from dataclasses import dataclass
import random
from collections import defaultdict
from enum import Enum
import uuid

class Layout(Enum):
    SQUARE = 1
    LINE = 2

@dataclass
class CellDefinition:
    '''
    uuid : unique identifier
    label: what is displayed on pyplots
    Grid position: refer to grid of all cells in the model and
        corresponds to locations in the environment. This is different from
        both display position and position within the layer.
    cell_number: which cell in the layer it is.
    layer_id: which layer the cell is in
    '''
    uuid: str
    label: str
    x_grid_position: int
    y_grid_position: int
    cell_number: int # bad name
    layer_id: str

    def export_network_information(self):
        return (self.label, self.x_grid_position, self.y_grid_position)

@dataclass
class SynapseDefinition:
    pre_cell_id: str
    post_cell_id: str
    starting_strength: float

@dataclass
class NetworkDefinition:
    cell_definitions: list
    synapse_definitions: list
    last_layer_x_grid_position: int

    def export_as_tuples(self):
        cells_by_uuid = {}
        cell_infos = []
        for cell in self.cell_definitions:
            cells_by_uuid[cell.uuid] = cell
            cell_infos.append(cell.export_network_information())
        synapse_infos = []
        for synapse in self.synapse_definitions:
            pre_cell = cells_by_uuid[synapse.pre_cell_id]
            post_cell = cells_by_uuid[synapse.post_cell_id]
            synapse_info = (pre_cell.label,
                            post_cell.label,
                            synapse.starting_strength)
            synapse_infos.append(synapse_info)
        return cell_infos, synapse_infos


class Layer:
    def __init__(self, id, size, starting_x_position, layout=Layout.LINE):
        self.id = id
        self.size = size
        self.layout = layout
        self.starting_x_position = starting_x_position
        self.edge_length = self._layer_edge_length()

    def _layer_edge_length(self):
        if self.layout == Layout.LINE:
            return 1
        
        sqrt = utils.newtons_square_root(self.size)
        if sqrt**2 == self.size:
            return sqrt
        return sqrt + 1

    def cell_layer_position(self, cell_number):
        if self.layout == Layout.LINE:
            return (0, cell_number,)

        x = cell_number % self.edge_length
        y = cell_number // self.edge_length
        return (x, y,)

    def cell_grid_position(self, cell_number):
        (layer_position_x, layer_position_y, ) = self.cell_layer_position(cell_number)
        return self.starting_x_position + layer_position_x, layer_position_y


@dataclass
class LayerConnection:
    pre_layer: Layer
    post_layer: Layer
    degree: float
    
def build_layer_based_network(layer_definitions, layer_connections):
    layers = layers_from_definitons(layer_definitions)
    return network_from_layers(layers, layer_connections)

def layers_from_definitons(layer_definitions):
    layers = []
    starting_x_position = 0
    for layer_definition in layer_definitions:
        (id, size, layout) = layer_definition
        layer = Layer(id, size, starting_x_position, layout)
        layers.append(layer)
        starting_x_position += layer.edge_length + 2
    return layers

def network_from_layers(layers, layer_connections):
    cell_definitions = []
    cell_definitions_by_layer = defaultdict(list)
    for layer in layers:
        for cell_number in range(layer.size):
            (x_grid_position, y_grid_position,) = layer.cell_grid_position(cell_number)
            # shit way to make string
            label = layer.id + "_" +  str(cell_number)
            cell_definition = CellDefinition(str(uuid.uuid4()), label,
                                          x_grid_position, y_grid_position,
                                          cell_number, layer.id)
            cell_definitions.append(cell_definition)
            cell_definitions_by_layer[layer.id].append(cell_definition)

    synapse_definitions = []
    for (pre_layer, post_layer, probability, synapse_strength) in layer_connections:
        for cell_definition_pre_layer in cell_definitions_by_layer[pre_layer]:
            for cell_definition_post_layer in cell_definitions_by_layer[post_layer]:
                if probability >= random.random():
                    synapse_definition = SynapseDefinition(cell_definition_pre_layer.uuid,
                                                           cell_definition_post_layer.uuid,
                                                           synapse_strength)
                    synapse_definitions.append(synapse_definition)
    return NetworkDefinition(cell_definitions,
                             synapse_definitions,
                             layers[-1].starting_x_position)

# needs test and to validate input
# also not sure if our actual graph data structure is the best way to compute
# this is just a dumb function
# horrible name
def network_from_tuples(cells,
                        synapses):
    '''
    This function is just to get us to classes from tuples
    '''

    cell_definitions = []
    cells_by_label = {}
    for (label, (x_grid_pos, y_grid_pos,),) in cells:
        cell_definition = CellDefinition(str(uuid.uuid4()), label,
                                            x_grid_pos, y_grid_pos, None, None)
        cell_definitions.append(cell_definition)
        cells_by_label[label] = cell_definition

    synapse_definitions = []
    for (pre_cell_label, post_cell_label, strength) in  synapses:
        pre_cell = cells_by_label[pre_cell_label]
        post_cell = cells_by_label[post_cell_label]
        synapse_definition = SynapseDefinition(pre_cell.uuid, post_cell.uuid, strength)
        synapse_definitions.append(synapse_definition)

    # Would be for reward but we are not using layers when building networks of single cells.
    last_layer_x_grid_position = None
    return NetworkDefinition(cell_definitions,
                             synapse_definitions,
                             last_layer_x_grid_position)


# eventually these should take a strength scaler parameter from the model
def small_default_network():
    cells = [("a", (0, 0),),
             ("b", (1, 0),),
             ("c", (2, 0),), ("d", (2, 1)),
             ("e", (3, 0),)]
    synapses = [("a", "b", 0.15),
                ("b", "c", 0.15),
                ("b", "d", 0.15),
                ("c", "e", 0.15),
                ("d", "e", 0.15),]
    return network_from_tuples(cells,
                               synapses)

def stdp_test_network():
    cells = [("a", (0, 0),),
             ("b", (1, 0),),
             ("c", (2, 0),)]
    synapses = [("a", "c", 0.05),
                ("b", "c", 0.05),]
    return network_from_tuples(cells,
                               synapses)


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
