from brains.network import NetworkDefinition

from dataclasses import dataclass, asdict, field

@dataclass
class CellTypeParameters:
    voltage_decay: float = 0.01
    current_decay: float = 0.03
    calcium_decay: float = 0.1
    starting_membrane_voltage: float = 0.0
    max_voltage: float = 1.0
    voltage_reset: float = -1.0
    calcium_increment: float = 1.0
    input_current_reset: float = 0.0
    starting_calcium: float = 0.0
    starting_input_current: float = 0.0
    reset_input_current: bool = True

@dataclass
class SynapseTypeParameters:
    stdp_scalar: float = 0.01
    max_strength: float = 0.06
    min_strength: float = 0.0
    starting_s_tag: float = 0.0
    noise_factor: float = 0.0

@dataclass
class ModelParameters:
    step_size: int = 1
    starting_dopamine: float = 1.0
    dopamine_decay: float = 0.0
    cell_type_parameters: CellTypeParameters = field(default_factory=CellTypeParameters)
    synapse_type_parameters: SynapseTypeParameters = field(default_factory=SynapseTypeParameters)
    epoch_length: int = 400
    epoch_delay: int = 50
    
    def __post_init__(self):
        '''
        Used to easily construct object from an exported dict.
        '''
        if isinstance(self.cell_type_parameters, dict):
            self.cell_type_parameters = CellTypeParameters(**self.cell_type_parameters)
        if isinstance(self.synapse_type_parameters, dict):
            self.synapse_type_parameters = SynapseTypeParameters(**self.synapse_type_parameters)


def handwriting_model_parameters(epoch_length=400,
                                 epoch_delay=50):
    synapse_type_paramenters = SynapseTypeParameters(noise_factor=0.5)
    return ModelParameters(starting_dopamine=0.0,
                           dopamine_decay=0.1,
                           synapse_type_parameters=synapse_type_paramenters,
                           epoch_length=epoch_length,
                           epoch_delay=epoch_delay)

def import_model(blob, model_module):
    network_definition = NetworkDefinition(**blob["network_definition"])
    model_parameters = ModelParameters(**blob["model_parameters"])
    return model_module.SimpleModel(network_definition, model_parameters)
