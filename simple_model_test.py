import simple_model
import unittest

class TestStringMethods(unittest.TestCase):

    def test_voltage_decay(self):
        '''
        Ensure potential falls with time.
        '''
        cell_type_parameters = simple_model.CellTypeParameters(voltage_decay = 0.1,
                                                               current_decay = 0,
                                                               calcium_decay = 0,
                                                               starting_membrane_voltage = 0.5)
        step_size = 1
        membrane = simple_model.CellMembrane(cell_type_parameters, step_size)        
        for _ in range(2):
            membrane.update()
        self.assertTrue(membrane.voltage() < 0.5)

if __name__ == '__main__':
    unittest.main()
