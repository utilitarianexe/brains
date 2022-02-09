from dataclasses import dataclass
import random
from collections import defaultdict

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

@dataclass
class Layer:
    neme: str
    size: int

# other ways to do this to
@dataclass
class LayerConnection:
    pre_layer: Layer
    post_layer: Layer
    degree: float

def build_layer_based_network(layers, layer_connections, cell_id_with_fake_input):
    synapse_end_points, cell_id_and_grid_positions  = edge_list_from_layers(layers, layer_connections)
    return network_from_edge_list(cell_id_and_grid_positions,
                                  synapse_end_points,
                                  cell_id_with_fake_input)


def edge_list_from_layers(layers, layer_connections):
    cell_id_and_grid_positions = []
    cell_ids_by_layer = defaultdict(list)
    for layer_number, (layer_id, size,) in enumerate(layers):
        for i in range(size):
            cell_id = (layer_id, i,)
            grid_position = layer_number, i
            cell_id_and_grid_positions.append((cell_id, grid_position,))
            cell_ids_by_layer[layer_id].append(cell_id)

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

# should not really be here
def default_network():
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
