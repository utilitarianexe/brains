from brains.network import LayerConnection, Layer, CellType, CellDefinition
from brains.network import network_from_layers, network_from_cells
import unittest


class TestBuildingNetwork(unittest.TestCase):

    def test_network_from_cells(self):
        cells = [CellDefinition("a", 0, 0),
                 CellDefinition("b", 1, 0),
                 CellDefinition("c", 2, 0), CellDefinition("d", 2, 1),
                 CellDefinition("e", 3, 0),]
        synapses = [("a", "b", 0.15),
                    ("b", "c", 0.15),
                    ("b", "d", 0.15),
                    ("c", "e", 0.15),
                    ("d", "e", 0.15),]
        network_definition = network_from_cells(cells, synapses)
        (cell_definitions, synapse_definitions, ) = network_definition.export_as_tuples()

        expected_cell_definitions = [("a", 0, 0),
                                     ("b", 1, 0),
                                     ("c", 2, 0), ("d", 2, 1),
                                     ("e", 3, 0)]
        self.assertCountEqual(cell_definitions, expected_cell_definitions)

        expected_synapses = [("a", "b", 0.15),
                             ("b", "c", 0.15),
                             ("b", "d", 0.15),
                             ("c", "e", 0.15),
                             ("d", "e", 0.15),]
        self.assertCountEqual(synapses, expected_synapses)


    def test_network_from_layers(self):
        layers = [Layer("a", 1, 0, 0, is_input_layer=True),
                  Layer("b", 2, 1, 0),
                  Layer("c", 1, 2, 0, is_output_layer=True),
                  ]
        layer_connections = [LayerConnection("a", "b", 0.1, 1),
                             LayerConnection("b", "c", 0.1, 1)]
        network_definition = network_from_layers(layers,
                                                 layer_connections)
        (cells, synapses,) = network_definition.export_as_tuples()

        expected_cells = [
            ("a_0", 0, 0),
            ("b_0", 1, 0),
            ("b_1", 1, 1),
            ("c_0", 2, 0)]
        self.assertCountEqual(cells, expected_cells)

        expected_synapses = [("a_0", "b_0", 0.1, False, 0.1, 0.002),
                             ("a_0", "b_1", 0.1, False, 0.1, 0.002),
                             ("b_0", "c_0", 0.1, False, 0.1, 0.002),
                             ("b_1", "c_0", 0.1, False, 0.1, 0.002),]
        self.assertCountEqual(synapses, expected_synapses)


if __name__ == '__main__':
    unittest.main()
