import brains.utils as utils

from dataclasses import dataclass, field
import random
from collections import defaultdict
from enum import IntEnum
import uuid
from collections import namedtuple

class Layout(IntEnum):
    LINE = 1
    SQUARE = 2

class CellType(IntEnum):
    EXCITATORY = 1
    INHIBITORY = 2
    MIXED = 3

@dataclass
class CellDefinition:
    '''
    Exported to files

    uuid : unique identifier
    label: what is displayed on pyplots
    Grid position: refer to grid of all cells in the model and
        corresponds to locations in the environment. This is different from
        both display position and position within the layer.
    cell_number: which cell in the layer it is.
    layer_id: which layer the cell is in
    '''
    label: str
    x_display_position: int
    y_display_position: int
    is_input_cell: bool = False
    x_input_position: int = 0
    y_input_position: int = 0
    is_output_cell: bool = False
    output_id: int = 0
    layer_id: str = ""
    cell_type: int = CellType.EXCITATORY
    target_fire_rate_per_epoch: float = 0.0
    input_balance: bool = False
    x_layer_position: int = 0
    y_layer_position: int = 0
    output_balance: bool = False
    lock_inhibition_strength: bool = False
    uuid: str = field(default_factory=lambda:str(uuid.uuid4()))

    def export_network_information(self):
        return (self.label, self.x_display_position, self.y_display_position)

@dataclass
class SynapseDefinition:
    '''
    Exported to files
    '''
    label: str
    pre_cell_id: str
    post_cell_id: str
    starting_strength: float = 0.0
    starting_inhibitory_strength: float = 0.0

@dataclass
class NetworkDefinition:
    '''
    Exported to files
    '''
    cell_definitions: list
    synapse_definitions: list

    def __post_init__(self):
        '''
        Used to easily construct object from an exported dict.
        '''
        new_cell_definitions = []
        for cell_definition in self.cell_definitions:
            if isinstance(cell_definition, dict):
                new_cell_definitions.append(CellDefinition(**cell_definition))
            else:
                new_cell_definitions.append(cell_definition)
        self.cell_definitions = new_cell_definitions
        
        new_synapse_definitions = []
        for synapse_definition in self.synapse_definitions:
            if isinstance(synapse_definition, dict):
                new_synapse_definitions.append(SynapseDefinition(**synapse_definition))
            else:
                new_synapse_definitions.append(synapse_definition)
        self.synapse_definitions = new_synapse_definitions

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

@dataclass
class LayerConnection:
    pre_layer: str
    post_layer: str
    synapse_strength: float = 0.0
    probability: float = 1.0

@dataclass
class Layer:
    '''
    Not exported to files.
    '''
    id: str
    size: int
    starting_x_position: int = 0
    starting_y_position: int = 0
    target_fire_rate_per_epoch: float = 0.0
    layout: int = Layout.LINE
    cell_type: int = CellType.EXCITATORY
    input_balance: bool = False
    is_input_layer: bool = False
    is_output_layer: bool = False
    output_balance: bool = False
    lock_inhibition_strength: bool = False

    def cell_layer_position(self, cell_number):
        if self.layout == Layout.LINE:
            return (0, cell_number,)

        x = cell_number % self.width()
        y = cell_number // self.width()
        return (x, y,)

    def width(self):
        if self.layout == Layout.LINE:
            return 1
        
        sqrt = utils.newtons_square_root(self.size)
        if sqrt**2 == self.size:
            return sqrt
        return sqrt + 1

    def height(self):
        if self.layout == Layout.LINE:
            return self.size
        else:
            return self.width()

    def cell_input_position(self, cell_number):
        if not self.is_input_layer:
            # kinda ugly
            return 0, 0
        return self.cell_layer_position(cell_number)

    def cell_display_position(self, cell_number):
        (layer_position_x, layer_position_y, ) = self.cell_layer_position(cell_number)
        display_x_position = self.starting_x_position + layer_position_x
        display_y_position = layer_position_y + self.starting_y_position
        return display_x_position, display_y_position

def add_display_position_to_layers(layers):
    previous_height = 0
    previous_width = 0
    previous_x_position = 0
    first = True
    for layer in layers:
        if first:
            starting_x_position = 0
            starting_y_position = 0
            first = False
        elif layer.cell_type == CellType.INHIBITORY:
            starting_x_position = previous_x_position
            starting_y_position = previous_height + 2
        else:
            starting_x_position = previous_width + previous_x_position + 2
            starting_y_position = 0            

        layer.starting_x_position = starting_x_position
        layer.starting_y_position = starting_y_position
        previous_height = layer.height()
        previous_x_position = starting_x_position
        previous_width =  layer.width()

def network_from_layers(layers, layer_connections):
    cell_definitions = []
    cell_definitions_by_layer = defaultdict(list)
    for layer in layers:
        for cell_number in range(layer.size):
            (x_display_position, y_display_position,) = layer.cell_display_position(
                cell_number)
            (x_input_position, y_input_position,) = layer.cell_input_position(cell_number)
            (x_layer_position, y_layer_position,) = layer.cell_layer_position(cell_number)
            label = f"{layer.id}_{cell_number}"
            cell_definition = CellDefinition(label,
                                             x_display_position, y_display_position,
                                             layer.is_input_layer,
                                             x_input_position, y_input_position,
                                             layer.is_output_layer,
                                             cell_number,
                                             layer.id, layer.cell_type,
                                             layer.target_fire_rate_per_epoch,
                                             layer.input_balance,
                                             x_layer_position, y_layer_position,
                                             layer.output_balance,
                                             layer.lock_inhibition_strength)
            cell_definitions.append(cell_definition)
            cell_definitions_by_layer[layer.id].append(cell_definition)

    synapse_definitions = []
    for layer_connection in layer_connections:
        for cell_definition_pre_layer in cell_definitions_by_layer[layer_connection.pre_layer]:
            for cell_definition_post_layer in cell_definitions_by_layer[layer_connection.post_layer]:
                if layer_connection.probability >= random.random():
                    if cell_definition_pre_layer.cell_type == CellType.MIXED:
                        negative_synapse_strength = layer_connection.synapse_strength
                        positive_synapse_strength = layer_connection.synapse_strength
                    if cell_definition_pre_layer.cell_type == CellType.EXCITATORY:
                        positive_synapse_strength = layer_connection.synapse_strength
                        negative_synapse_strength = 0.0
                    if cell_definition_pre_layer.cell_type == CellType.INHIBITORY:
                        negative_synapse_strength = layer_connection.synapse_strength
                        positive_synapse_strength = 0.0
                    label = f"{cell_definition_pre_layer.label}_to_{cell_definition_post_layer.label}"
                    synapse_definition = SynapseDefinition(
                        label,
                        cell_definition_pre_layer.uuid,
                        cell_definition_post_layer.uuid,
                        positive_synapse_strength,
                        negative_synapse_strength)
                    synapse_definitions.append(synapse_definition)
    return NetworkDefinition(cell_definitions,
                             synapse_definitions)

def network_from_cells(cell_definitions,
                       synapses):
    cell_definitions_by_label = {}
    for definition in cell_definitions:
        cell_definitions_by_label[definition.label] = definition

    synapse_definitions = []
    for (pre_cell_label, post_cell_label, strength) in  synapses:
        pre_cell_definition = cell_definitions_by_label[pre_cell_label]
        post_cell_definition = cell_definitions_by_label[post_cell_label]
        label = f"{pre_cell_definition.label}_to_{post_cell_definition.label}"
        synapse_definition = SynapseDefinition(label,
                                               pre_cell_definition.uuid,
                                               post_cell_definition.uuid,
                                               strength, strength)
        synapse_definitions.append(synapse_definition)

    return NetworkDefinition(cell_definitions,
                             synapse_definitions)

# eventually these should take a strength scaler parameter from the model
def small_default_network():
    cells = [CellDefinition("a", 0, 0),
             CellDefinition("b", 1, 0),
             CellDefinition("c", 2, 0), CellDefinition("d", 2, 1),
             CellDefinition("e", 3, 0)]
    synapses = [("a", "b", 0.15),
                ("b", "c", 0.15),
                ("b", "d", 0.15),
                ("c", "e", 0.15),
                ("d", "e", 0.15),]
    return network_from_cells(cells,
                              synapses)

def stdp_test_network(input_balance=False):
    cells = [CellDefinition("a", 0, 0,
                            x_input_position=0,
                            y_input_position=0,
                            is_input_cell=True,
                            input_balance=input_balance,
                            target_fire_rate_per_epoch=1.0),
             CellDefinition("b", 1, 0,
                            x_input_position=1,
                            y_input_position=0,
                            is_input_cell=True,
                            input_balance=input_balance,
                            target_fire_rate_per_epoch=1.0),
             CellDefinition("c", 2, 0,
                            input_balance=input_balance,
                            target_fire_rate_per_epoch=1.0),]
    synapses = [("a", "c", 0.05),
                ("b", "c", 0.05),]
    return network_from_cells(cells,
                              synapses)

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

def mnist_network():
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
              Layer("b", 6*6,
                    layout = Layout.SQUARE,
                    target_fire_rate_per_epoch = 0.1,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = True),
              Layer("c", 10,
                    layout = Layout.LINE,
                    is_output_layer = True,
                    target_fire_rate_per_epoch = 0.1,
                    input_balance = True,
                    output_balance = True,
                    lock_inhibition_strength = False)]

    layer_connections = [LayerConnection("a", "b", 0.00035),
                         LayerConnection("i", "b", 0.00035),
                         LayerConnection("b", "c", 0.001)]
    add_display_position_to_layers(layers)
    return network_from_layers(layers, layer_connections)

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
