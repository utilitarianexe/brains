from dataclasses import dataclass

@dataclass
class PerCellParameters:
    name: str
    x_grid_position: int
    y_grid_position: int

@dataclass
class PerSynapseParameters:
    pre_cell_name: str
    post_cell_name: str

@dataclass
class NetworkDefinition:
    per_cell_parameters: list
    per_synapse_parameters: list
    cell_name_with_fake_input: str



def default_network():
    cell_name_and_grid_position = [("a", (0, 0)),
                                   ("b", (1, 0)),
                                   ("c", (2, 0)), ("d", (2, 1)),
                                   ("e", (3, 0))]
    synapse_end_points = [("a", "b"),
                          ("b", "c"),
                          ("b", "d"),
                          ("c", "e"),
                          ("d", "e"),]
    cell_name_with_fake_input = "a"
    return network_from_edge_list(cell_name_and_grid_position,
                                  synapse_end_points,
                                  cell_name_with_fake_input)

# need to use consistant quotes
def edge_list_from_layers():
    layers = [{'size': 10, 'connections': [{"name": "x", "type": "all"}, ]}]
                         
# needs test and to validate input
# also not sure if our actual graph data structure is the best way to compute
def network_from_edge_list(cell_name_and_grid_position,
                           synapse_end_points,
                           cell_name_with_fake_input):
    '''
    Grid position is purely for display
    '''

    # dont like how we are doing plurals
    per_cell_parameters = []
    for (cell_name, (x_grid_pos, y_grid_pos)) in cell_name_and_grid_position:
        cell_parameters = PerCellParameters(cell_name, x_grid_pos, y_grid_pos)
        per_cell_parameters.append(cell_parameters)

    per_synapse_parameters = []
    for (pre_cell_name, post_cell_name) in synapse_end_points:
        per_synapse_parameters.append(PerSynapseParameters(pre_cell_name, post_cell_name))
        
    return NetworkDefinition(per_cell_parameters,
                             per_synapse_parameters,
                             cell_name_with_fake_input)
