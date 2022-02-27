import network
import environment
import simple_model
import example_model

def simple_model_stdp():
    step_size = 1
    starting_dopamine = 1.0
    dopamine_decay = 0.0
    model_parameters = simple_model.ModelParameters(step_size,
                                                    starting_dopamine, dopamine_decay)
    
    starting_membrane_voltage = 0
    voltage_decay = 0.01
    input_decay = 0.03
    calcium_decay  = 0.1
    cell_type_parameters = simple_model.CellTypeParameters(voltage_decay, input_decay, calcium_decay,
                                                           starting_membrane_voltage)
    
    stdp_scalar = 0.001
    reward_scalar = 0.1
    synapse_max_strength = 0.4
    synapse_min_strength = 0.0
    s_tag_decay_rate = 0.003
    synapse_type_parameters = simple_model.SynapseTypeParameters(stdp_scalar, reward_scalar,
                                                                 synapse_max_strength,
                                                                 synapse_min_strength,
                                                                 s_tag_decay_rate)

    # need like some kind of average starting connection strength thing
    network_definition = network.stdp_test_network()
    model_environment = environment.STDPTestEnvironment()

    return simple_model.SimpleModel(cell_type_parameters, synapse_type_parameters,
                                    network_definition, model_environment,
                                    model_parameters)

def simple_model_handwriting():
    step_size = 1
    starting_dopamine = 1
    dopamine_decay = 0.1
    model_parameters = simple_model.ModelParameters(step_size,
                                                    starting_dopamine, dopamine_decay)

    starting_membrane_voltage = 0
    voltage_decay = 0.01
    input_decay = 0.03
    calcium_decay  = 0.1
    cell_type_parameters = simple_model.CellTypeParameters(voltage_decay, input_decay, calcium_decay,
                                                           starting_membrane_voltage)

    stdp_scalar = 0.001
    reward_scalar = 0.1
    synapse_max_strength = 0.4
    synapse_min_strength = 0.0
    s_tag_decay_rate = 0.003
    synapse_type_parameters = simple_model.SynapseTypeParameters(stdp_scalar, reward_scalar,
                                                                 synapse_max_strength,
                                                                 synapse_min_strength,
                                                                 s_tag_decay_rate)

    # need like some kind of average starting connection strength thing
    network_definition = network.layer_based_default_network()
    model_environment = environment.HandwritenEnvironment(delay=50, frequency=150,
                                                          image_lines=None, shuffle=True)

    return simple_model.SimpleModel(cell_type_parameters, synapse_type_parameters,
                                    network_definition, model_environment,
                                    model_parameters)

def default_example_model():
    return example_model.ExampleModel()

