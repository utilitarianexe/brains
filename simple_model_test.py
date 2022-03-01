import simple_model
import unittest

class TestCell(unittest.TestCase):

    def test_voltage_decay(self):
        '''
        Ensure potential falls with time.
        '''
        cell_type_parameters = simple_model.CellTypeParameters(voltage_decay = 0.1,
                                                               current_decay = 0.0,
                                                               calcium_decay = 0.0,
                                                               starting_membrane_voltage = 0.5)
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
        cell_type_parameters = simple_model.CellTypeParameters(voltage_decay = 0.01,
                                                               current_decay = 0.5,
                                                               calcium_decay = 0.0,
                                                               starting_membrane_voltage = 0.0)
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

if __name__ == '__main__':
    unittest.main()
