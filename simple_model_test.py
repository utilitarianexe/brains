import default_runs
import environment
import network
import simple_model

import unittest

class TestCellMembrane(unittest.TestCase):

    def test_voltage_decay(self):
        '''
        Ensure potential falls with time.
        '''
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        cell_type_parameters.starting_membrane_voltage = 0.5
        step_size = 1
        membrane = simple_model.CellMembrane(cell_type_parameters, step_size)
        membrane.update()
        membrane.update()
        self.assertTrue(membrane.voltage() < 0.5)

    def test_one_spike_input(self):
        '''
        Cell should not fire until after voltage builds up from input. It should fire once
        and then not fire again as input decays or is reset.
        '''
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        step_size = 1
        membrane = simple_model.CellMembrane(cell_type_parameters, step_size)        

        self.assertFalse(membrane.fired())
        membrane.receive_input(0.8)
        membrane.update()
        self.assertFalse(membrane.fired())
        membrane.update()
        self.assertFalse(membrane.fired())
        membrane.update()
        self.assertTrue(membrane.fired())
        membrane.update()
        self.assertFalse(membrane.fired())
        membrane.update()
        self.assertFalse(membrane.fired())

class TestModel(unittest.TestCase):
    def two_cell_model(self, fire_points, synapse_strength):
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        synapse_type_parameters = default_runs.simple_model_stdp_synapse_type_parameters()
        model_parameters = default_runs.simple_model_stdp_model_parameters(cell_type_parameters,
                                                                           synapse_type_parameters)
        cells = [("a", (0, 0),),
                 ("b", (1, 0),)]
        synapses = [("a", "b", synapse_strength)]
        model_network = network.network_from_tuples(cells,
                                              synapses)
        model_environment = environment.TestEnvironment(fire_points)
        return simple_model.SimpleModel(model_network, model_environment,
                                         model_parameters)
        
    def test_spike_propogation(self):
        '''
        Causing one cell to spike should cause the next to spike
        '''
        model = self.two_cell_model([(1, 0, 0, 0.15)], 0.1)
        fire_history = []
        for i in range(100):
            model.step(i)
            outputs = model.outputs()
            # clearly we need a nicer output system
            if outputs["a"] > 1:
                fire_history.append("a")
            if outputs["b"] > 1:
                fire_history.append("b")

        expected_fire_history = ["a", "b"]
        self.assertEqual(fire_history, expected_fire_history)

    def test_stdp_pre_post(self):
        '''
        Pre fire before post should cause the connection to get stronger.
        '''
        fire_points = [(0, 0, 0, 0.15),
                       (10, 1, 0, 0.15),
                       (100, 0, 0, 0.15),
                       (110, 1, 0, 0.15),
                       ]
        starting_synapse_strength = 0.0
        model = self.two_cell_model(fire_points, starting_synapse_strength)
        fire_history = []
        for i in range(200):
            model.step(i)
        self.assertGreater(model.synapses[0].strength, starting_synapse_strength)

    def test_stdp_post_pre(self):
        '''
        Post fire before pre fire should cause the connection to get weaker.
        '''
        fire_points = [(10, 0, 0, 0.15),
                       (0, 1, 0, 0.15),
                       (110, 0, 0, 0.15),
                       (100, 1, 0, 0.15),
                       ]
        starting_synapse_strength = 0.01
        model = self.two_cell_model(fire_points, starting_synapse_strength)
        fire_history = []
        for i in range(200):
            model.step(i)
        self.assertLess(model.synapses[0].strength, starting_synapse_strength)

if __name__ == '__main__':
    unittest.main()
