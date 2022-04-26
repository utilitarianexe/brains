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
    uuid: str = field(default_factory=lambda:str(uuid.uuid4()))

    def export_network_information(self):
        return (self.label, self.x_display_position, self.y_display_position)

@dataclass
class SynapseDefinition:
    '''
    Exported to files
    '''
    pre_cell_id: str
    post_cell_id: str
    starting_strength: float
    label: str

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


# convenience tuple
LayerDefinition = namedtuple('LayerDefinition',
                             'label size layout cell_type input_balance target_fire_rate_per_epoch '\
                             'is_input_layer is_output_layer')

class Layer:
    '''
    Convenience class not exported to files.
    '''
    def __init__(self, id, size,
                 starting_x_position, starting_y_position,
                 target_fire_rate_per_epoch=0.0,
                 layout=Layout.LINE, cell_type=CellType.EXCITATORY,
                 input_balance=False,
                 is_input_layer=False, is_output_layer=False):
        self.id = id
        self.size = size
        self.layout = layout
        self.starting_x_position = starting_x_position
        self.starting_y_position = starting_y_position
        self.cell_type = cell_type
        self.target_fire_rate_per_epoch = target_fire_rate_per_epoch
        self.input_balance = input_balance
        self.is_input_layer = is_input_layer
        self.is_output_layer = is_output_layer

    def _cell_layer_position(self, cell_number):
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
        return self._cell_layer_position(cell_number)

    def cell_display_position(self, cell_number):
        (layer_position_x, layer_position_y, ) = self._cell_layer_position(cell_number)
        return self.starting_x_position + layer_position_x, layer_position_y + self.starting_y_position

def build_layer_based_network(layer_definitions, layer_connections):
    layers = layers_from_definitons(layer_definitions)
    return network_from_layers(layers, layer_connections)

def layers_from_definitons(layer_definitions):
    layers = []
    previous_height = 0
    previous_width = 0
    previous_x_position = 0
    for definition in layer_definitions:
        if definition.cell_type == CellType.INHIBITORY:
            starting_x_position = previous_x_position
            starting_y_position = previous_height + 2
        else:
            starting_x_position = previous_width + previous_x_position + 2
            starting_y_position = 0

        layer = Layer(definition.label, definition.size,
                      starting_x_position, starting_y_position,
                      target_fire_rate_per_epoch=definition.target_fire_rate_per_epoch,
                      layout=definition.layout, cell_type=definition.cell_type,
                      input_balance=definition.input_balance,
                      is_input_layer=definition.is_input_layer,
                      is_output_layer=definition.is_output_layer)
        layers.append(layer)
        previous_height = layer.height()
        previous_x_position = starting_x_position
        previous_width =  layer.width()

    return layers

def network_from_layers(layers, layer_connections):
    cell_definitions = []
    cell_definitions_by_layer = defaultdict(list)
    for layer in layers:
        for cell_number in range(layer.size):
            (x_display_position, y_display_position,) = layer.cell_display_position(cell_number)
            (x_input_position, y_input_position,) = layer.cell_input_position(cell_number)
            label = f"{layer.id}_{cell_number}"
            cell_definition = CellDefinition(label,
                                             x_display_position, y_display_position,
                                             layer.is_input_layer,
                                             x_input_position, y_input_position,
                                             layer.is_output_layer,
                                             cell_number,
                                             layer.id, layer.cell_type,
                                             layer.target_fire_rate_per_epoch,
                                             layer.input_balance)
            cell_definitions.append(cell_definition)
            cell_definitions_by_layer[layer.id].append(cell_definition)

    synapse_definitions = []
    for (pre_layer, post_layer, probability, synapse_strength) in layer_connections:
        for cell_definition_pre_layer in cell_definitions_by_layer[pre_layer]:
            for cell_definition_post_layer in cell_definitions_by_layer[post_layer]:
                if probability >= random.random():
                    label = f"{cell_definition_pre_layer.label}_to_{cell_definition_post_layer.label}"
                    synapse_definition = SynapseDefinition(cell_definition_pre_layer.uuid,
                                                           cell_definition_post_layer.uuid,
                                                           synapse_strength,
                                                           label)
                    synapse_definitions.append(synapse_definition)
    return NetworkDefinition(cell_definitions,
                             synapse_definitions)

# needs test and to validate input
# also not sure if our actual graph data structure is the best way to compute
# this is just a dumb function
# horrible name
def network_from_tuples(cell_definitions,
                        synapses):
    '''
    This function is just to get us to classes from tuples
    '''

    cell_definitions_by_label = {}
    for definition in cell_definitions:
        cell_definitions_by_label[definition.label] = definition

    synapse_definitions = []
    for (pre_cell_label, post_cell_label, strength) in  synapses:
        pre_cell_definition = cell_definitions_by_label[pre_cell_label]
        post_cell_definition = cell_definitions_by_label[post_cell_label]
        label = f"{pre_cell_definition.label}_to_{post_cell_definition.label}"
        synapse_definition = SynapseDefinition(pre_cell_definition.uuid, post_cell_definition.uuid,
                                               strength, label)
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
    return network_from_tuples(cells,
                               synapses)

def stdp_test_network(input_balance=False):
    cells = [CellDefinition("a", 0, 0,
                            x_input_position=0,
                            y_input_position=0,
                            is_input_cell=True,
                            input_balance=input_balance, target_fire_rate_per_epoch=1.0),
             CellDefinition("b", 1, 0,
                            x_input_position=1,
                            y_input_position=0,
                            is_input_cell=True,
                            input_balance=input_balance, target_fire_rate_per_epoch=1.0),
             CellDefinition("c", 2, 0, input_balance=input_balance, target_fire_rate_per_epoch=1.0),]
    synapses = [("a", "c", 0.05),
                ("b", "c", 0.05),]
    return network_from_tuples(cells,
                               synapses)

def layer_based_default_network():
    image_size = 28*28
    layers = [LayerDefinition("a", image_size, Layout.SQUARE,
                              CellType.EXCITATORY, False, 0.0, True, False),
              LayerDefinition("i", image_size, Layout.SQUARE,
                              CellType.INHIBITORY, False, 0.0, True, False),
              LayerDefinition("b", 6*6, Layout.SQUARE, CellType.EXCITATORY, True, 0.2, False, False),
              LayerDefinition("c", 2, Layout.LINE, CellType.EXCITATORY, True, 0.5, False, True)]
    
    # Something about connection probability rubs me wrong.
    # connections might be more complex
    layer_connections = [("a", "b", 1, 0.01,),
                         ("i", "b", 1, 0.01,),
                         ("b", "c", 1, 0.006,)]
    return build_layer_based_network(layers, layer_connections)

def easy_layer_simple_network():
    layers = [LayerDefinition("a", 3, Layout.LINE, CellType.EXCITATORY, False, 0.0, True, False),
              LayerDefinition("b", 2, Layout.LINE, CellType.EXCITATORY, False, 0.0, False, True)]
    
    layer_connections = [("a", "b", 1, 0.035)]
    return build_layer_based_network(layers, layer_connections)

def easy_layer_network():
    layers = [LayerDefinition("a", 3, Layout.LINE, CellType.EXCITATORY, False, 0.0, True, False),
              LayerDefinition("i", 3, Layout.LINE, CellType.INHIBITORY, False, 0.0, True, False),
              LayerDefinition("b", 4, Layout.LINE, CellType.EXCITATORY, True, 0.25, False, False),
              LayerDefinition("c", 2, Layout.LINE, CellType.EXCITATORY, True, 0.5, False, True)]

    layer_connections = [("a", "b", 1, 0.1),
                         ("i", "b", 1, 0.1),
                         ("b", "c", 1, 0.05),]
    return build_layer_based_network(layers, layer_connections)

