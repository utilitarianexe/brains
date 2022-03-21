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
    def two_cell_network(self, starting_synapse_strength):
        cells = [("a", (0, 0),),
                 ("b", (1, 0),)]
        synapses = [("a", "b", starting_synapse_strength)]
        return network.network_from_tuples(cells,
                                           synapses)

    def two_cell_model(self, fire_points, reward_ranges, starting_synapse_strength):
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        synapse_type_parameters = default_runs.simple_model_stdp_synapse_type_parameters()
        model_parameters = default_runs.simple_model_stdp_model_parameters(cell_type_parameters,
                                                                           synapse_type_parameters)
        model_environment = environment.TestEnvironment(fire_points, reward_ranges)
        return simple_model.SimpleModel(self.two_cell_network(starting_synapse_strength),
                                        model_environment,
                                        model_parameters)
        
    def test_spike_propogation(self):
        '''
        Causing one cell to spike should cause the next to spike
        '''
        model = self.two_cell_model([(1, 0, 0, 0.15)], [], 0.1)
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
        model = self.two_cell_model(fire_points, [], starting_synapse_strength)
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
        model = self.two_cell_model(fire_points, [], starting_synapse_strength)
        fire_history = []
        for i in range(200):
            model.step(i)
        self.assertLess(model.synapses[0].strength, starting_synapse_strength)

    def test_rewarded_stdp(self):
        '''
        Pre fire before post should cause the connection to get stronger.
        '''
        fire_points = [(0, 0, 0, 0.15),
                       (10, 1, 0, 0.15),
                       (100, 0, 0, 0.15),
                       (110, 1, 0, 0.15),
                       (200, 0, 0, 0.15),
                       (210, 1, 0, 0.15),
                       (310, 0, 0, 0.15),
                       (300, 1, 0, 0.15),
                       (410, 0, 0, 0.15),
                       (400, 1, 0, 0.15),
                       ]
        reward_ranges =  [(1, 0, [205, 230])]
        model_environment = environment.TestEnvironment(fire_points, reward_ranges)
                
        starting_synapse_strength = 0.0
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        synapse_type_parameters = default_runs.simple_model_stdp_synapse_type_parameters()
        step_size = 1
        starting_dopamine = 0.0
        dopamine_decay = 0.1
        model_parameters = simple_model.ModelParameters(step_size,
                                                        starting_dopamine, dopamine_decay,
                                                        cell_type_parameters, synapse_type_parameters)
        model = simple_model.SimpleModel(self.two_cell_network(starting_synapse_strength),
                                         model_environment,
                                         model_parameters)


        fire_history = []
        for i in range(500):
            if i == 150:
                self.assertEqual(model.synapses[0].strength, starting_synapse_strength)
            if i == 250:
                self.assertGreater(model.synapses[0].strength, starting_synapse_strength)
            model.step(i)

    def test_stdp_auto_input_selection(self):
        '''
        Intializes a network of two input cells connected to an ouput cell. The input cells fire in
        close sequence. And both are required to trigger the output cell.

        Both synapses should get stronger at first. But eventually the first cell to fire should be
        strong enough to trigger the output cell on its before the second input cell fires. After this
        point the synapse of the first input will continue to get stonger while the second will get
        weaker because it fires after the output cell.
        '''
        cell_type_parameters = default_runs.simple_model_stdp_cell_type_parameters()
        synapse_type_parameters = default_runs.simple_model_stdp_synapse_type_parameters()
        model_parameters = default_runs.simple_model_stdp_model_parameters(cell_type_parameters,
                                                              synapse_type_parameters)
        network_definition = network.stdp_test_network()
        model_environment = environment.STDPTestEnvironment()
        model =  simple_model.SimpleModel(network_definition, model_environment,
                                          model_parameters)
        synapses_by_pre_cell = {}
        for synapse in model.synapses:
            synapses_by_pre_cell[synapse.pre_cell.label] = synapse
        synapse_early_input = synapses_by_pre_cell["a"]
        synapse_late_input = synapses_by_pre_cell["b"]
        starting_strength = synapse_early_input.strength 
            
        for i in range(15000):
            model.step(i)
            if i == 5000:
                self.assertTrue(synapse_early_input.strength > starting_strength)
                self.assertTrue(synapse_late_input.strength > synapse_early_input.strength)
        self.assertTrue(synapse_early_input.strength > synapse_late_input.strength)


if __name__ == '__main__':
    unittest.main()
