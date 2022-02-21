import network
import environment
import simple_model
import example_model

def simple_model_stdp():
    starting_membrane_voltage = 0
    voltage_decay = 0.01
    input_decay = 0.03
    calcium_decay  = 0.1
    step_size = 1
    stdp_scalar = 0.001
    starting_dopamine = 1
    dopamine_decay = 0
    
    # need like some kind of average starting connection strength thing
    cell_type_parameters = simple_model.CellTypeParameters(voltage_decay, input_decay, calcium_decay,
                                                           starting_membrane_voltage)
    synapse_type_parameters = simple_model.SynapseTypeParameters(stdp_scalar)

    network_definition = network.elf_network()
    model_environment = environment.ElfEnvironment()

    return simple_model.SimpleModel(cell_type_parameters, synapse_type_parameters,
                                    network_definition, model_environment,
                                    starting_dopamine, dopamine_decay,
                                    step_size)

def simple_model_handwriting():
    starting_membrane_voltage = 0
    voltage_decay = 0.01
    input_decay = 0.03
    calcium_decay  = 0.1
    step_size = 1
    stdp_scalar = 0.001
    starting_dopamine = 1
    dopamine_decay = 0.1
    
    # need like some kind of average starting connection strength thing
    cell_type_parameters = simple_model.CellTypeParameters(voltage_decay, input_decay, calcium_decay,
                                                           starting_membrane_voltage)
    synapse_type_parameters = simple_model.SynapseTypeParameters(stdp_scalar)

    network_definition = network.layer_based_default_network()
    model_environment = environment.HandwritenEnvironment()

    return simple_model.SimpleModel(cell_type_parameters, synapse_type_parameters,
                                    network_definition, model_environment,
                                    starting_dopamine, dopamine_decay,
                                    step_size)

def default_example_model():
    return example_model.ExampleModel()

