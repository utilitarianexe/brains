import network
import environment
import simple_model
import example_model

def default_simple_model():
    voltage_decay = 0.01
    input_decay = 0.1
    step_size = 1

    # not actually used
    starting_synapse_strength = 0.15
    
    cell_type_parameters = simple_model.CellTypeParameters(voltage_decay, input_decay, 0)
    synapse_type_parameters = simple_model.SynapseTypeParameters(starting_synapse_strength)

    # network_definition = network.small_default_network()
    # model_environment = environment.SimpleEnvironment()
    
    network_definition = network.layer_based_default_network()
    model_environment = environment.HandwritenEnvironment()

    return simple_model.SimpleModel(cell_type_parameters, synapse_type_parameters,
                                    network_definition, model_environment,
                                    step_size)

def default_example_model():
    return example_model.ExampleModel()

