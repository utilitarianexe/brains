import network
import environment
import simple_model
import example_model

import dataclasses

def simple_model_stdp_cell_type_parameters():
    starting_membrane_voltage = 0
    voltage_decay = 0.01
    input_decay = 0.03
    calcium_decay  = 0.1
    max_voltage = 1.0
    voltage_reset = -1.0
    calcium_increment = 1.0
    input_current_reset = 0.0
    starting_input_current = 0.0
    starting_calcium = 0.0
    reset_input_current = True
    return simple_model.CellTypeParameters(voltage_decay, input_decay, calcium_decay,
                                           starting_membrane_voltage, max_voltage,
                                           voltage_reset, calcium_increment,
                                           input_current_reset,
                                           starting_input_current,
                                           starting_calcium,
                                           reset_input_current)

def simple_model_stdp_synapse_type_parameters():
    stdp_scalar = 0.001
    reward_scalar = 0.1
    synapse_max_strength = 0.4
    synapse_min_strength = 0.0
    s_tag_decay_rate = 0.003
    starting_s_tag = 0.0
    return simple_model.SynapseTypeParameters(stdp_scalar, reward_scalar,
                                              synapse_max_strength,
                                              synapse_min_strength,
                                              s_tag_decay_rate,
                                              starting_s_tag)

def simple_model_stdp_model_parameters(cell_type_parameters, synapse_type_parameters):
    step_size = 1
    starting_dopamine = 1.0
    dopamine_decay = 0.0
    return simple_model.ModelParameters(step_size,
                                        starting_dopamine, dopamine_decay,
                                        cell_type_parameters, synapse_type_parameters)

def simple_model_stdp():
    cell_type_parameters = simple_model_stdp_cell_type_parameters()
    synapse_type_parameters = simple_model_stdp_synapse_type_parameters()
    model_parameters = simple_model_stdp_model_parameters(cell_type_parameters,
                                                          synapse_type_parameters)
    network_definition = network.stdp_test_network()
    model_environment = environment.STDPTestEnvironment()
    return simple_model.SimpleModel(network_definition, model_environment,
                                    model_parameters)

def simple_model_handwriting():
    cell_type_parameters = simple_model_stdp_cell_type_parameters()
    synapse_type_parameters = simple_model_stdp_synapse_type_parameters()

    step_size = 1
    starting_dopamine = 1
    dopamine_decay = 0.1
    model_parameters = simple_model.ModelParameters(step_size,
                                                    starting_dopamine, dopamine_decay,
                                                    cell_type_parameters, synapse_type_parameters)


    # need like some kind of average starting connection strength thing
    network_definition = network.layer_based_default_network()
    model_environment = environment.HandwritenEnvironment(
        delay=50, frequency=150,
        image_lines=None, shuffle=True,
        last_layer_x_grid_position=network_definition.last_layer_x_grid_position)

    return simple_model.SimpleModel(network_definition, model_environment,
                                    model_parameters)

def default_example_model():
    return example_model.ExampleModel()

