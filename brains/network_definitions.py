from brains.network import LayerConnection, Layer, CellType, CellDefinition, Layout
from brains.network import network_from_layers, network_from_cells, add_display_position_to_layers

def parameter_test_network():
    cells = [CellDefinition("a", 0, 0,
                            is_input_cell=True,
                            x_input_position=0,
                            y_input_position=0),
             CellDefinition("b", 0, 1,
                            is_input_cell=True,
                            x_input_position=0,
                            y_input_position=1),
             CellDefinition("c", 2, 0),]
    synapses = [("a", "c", 0.03),
                ("b", "c", 0.03),]
    return network_from_cells(cells,
                              synapses)

def stdp_test_network(input_balance=False):
    cells = [CellDefinition("a", 0, 0,
                            is_input_cell=True,
                            x_input_position=0,
                            y_input_position=0,
                            input_balance=input_balance,
                            target_fire_rate_per_epoch=1.0),
             CellDefinition("b", 1, 0,
                            is_input_cell=True,
                            x_input_position=1,
                            y_input_position=0,
                            target_fire_rate_per_epoch=1.0),
             CellDefinition("c", 2, 0,
                            input_balance=input_balance,
                            target_fire_rate_per_epoch=1.0),]
    synapses = [("a", "c", 0.026),
                ("b", "c", 0.026),]
    return network_from_cells(cells,
                              synapses)

def easy_layer_network():
    layers = [Layer("a", 3,
                    layout = Layout.LINE,
                    is_input_layer = True,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("i", 3,
                    layout = Layout.LINE,
                    is_input_layer = True,
                    cell_type = CellType.INHIBITORY,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("b", 4,
                    layout = Layout.LINE,
                    target_fire_rate_per_epoch = 0.25,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("c", 2,
                    layout = Layout.LINE,
                    is_output_layer = True,
                    target_fire_rate_per_epoch = 0.5,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False)]
    layer_connections = [LayerConnection("a", "b", 0.1),
                         LayerConnection("i", "b", 0.1),
                         LayerConnection("b", "c", 0.45),]
    add_display_position_to_layers(layers)
    return network_from_layers(layers, layer_connections)


def layer_based_default_network():
    '''
      Used for the x o world
    '''
    image_size = 28*28
    layers = [Layer("a", image_size,
                    layout = Layout.SQUARE,
                    is_input_layer = True,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("i", image_size,
                    layout = Layout.SQUARE,
                    is_input_layer = True,
                    cell_type = CellType.INHIBITORY,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("b", 6*6,
                    layout = Layout.SQUARE,
                    target_fire_rate_per_epoch = 0.2,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("c", 2,
                    layout = Layout.LINE,
                    is_output_layer = True,
                    target_fire_rate_per_epoch = 0.5,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False)
              ]
    
    layer_connections = [LayerConnection("a", "b", 0.01),
                         LayerConnection("i", "b", 0.01),
                         LayerConnection("b", "c", 0.006)]
    add_display_position_to_layers(layers)    
    return network_from_layers(layers, layer_connections)

def mnist_network(number_of_outputs=10):
    image_size = 28*28
    layers = [Layer("a", image_size,
                    layout = Layout.SQUARE,
                    is_input_layer = True,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = False),
              Layer("i", image_size,
                    layout = Layout.SQUARE,
                    is_input_layer = True,
                    cell_type = CellType.INHIBITORY,
                    input_balance = False,
                    output_balance = True,
                    lock_inhibition_strength = True),
              Layer("b", 30*30,
                    layout = Layout.SQUARE,
                    target_fire_rate_per_epoch = 0.1,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = True),
              Layer("c", number_of_outputs,
                    layout = Layout.LINE,
                    is_output_layer = True,
                    target_fire_rate_per_epoch = 1.0/number_of_outputs,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False)]

    layer_connections = [LayerConnection("a", "b", 0.046,
                                         define_by_inputs_per_cell=True,
                                         inputs_per_cell = 6,
                                         unsupervised_stdp = True,
                                         reward_scalar=0.02,
                                         s_tag_decay_rate = 0.1),
                         LayerConnection("i", "b", 0.00035),
                         LayerConnection("b", "c", 0.0008/number_of_outputs)]
    add_display_position_to_layers(layers)
    return network_from_layers(layers, layer_connections)

