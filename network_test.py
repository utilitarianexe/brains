from network import edge_list_from_layers, Layer, Layout
import unittest


class TestBuildingNetwork(unittest.TestCase):

    def test_edge_list_from_layers(self):
        '''
        '''
        layers = [Layer("a", 1, 0),
                  Layer("b", 2, 1),
                  Layer("c", 1, 2),
                  ]
        layer_connections = [("a", "b", 1, 0.1), ("b", "c", 1, 0.1)]
        per_synapse_tuple, per_cell_tuple = edge_list_from_layers(layers,
                                                                  layer_connections)
        expected_per_synapse_tuple = [(("a", 0,), ("b", 0,), 0.1, ),
                                       (("a", 0,), ("b", 1,), 0.1, ),
                                       (("b", 0,), ("c", 0,), 0.1, ),
                                       (("b", 1,), ("c", 0,), 0.1, ),]
        self.assertCountEqual(per_synapse_tuple, expected_per_synapse_tuple)

        expected_per_cell_tuple = [(("a", 0,), (0, 0,),),
                                   (("b", 0,), (1, 0,),),
                                   (("b", 1,), (1, 1,),),
                                   (("c", 0,), (2, 0,),),]
        self.assertCountEqual(per_cell_tuple, expected_per_cell_tuple)


if __name__ == '__main__':
    unittest.main()
