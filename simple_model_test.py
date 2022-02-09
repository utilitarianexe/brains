import simple_model
import unittest


# does not work anymore
class TestStringMethods(unittest.TestCase):

    def test_synapse_decay(self):
        '''
        Ensure potential falls with time.
        '''
        voltage = 1
        decay = 0.1
        step_size = 1
        strength = 1
        artificial_source = lambda x: 0
        synapse = simple_model.SimpleSynapse(decay, step_size, voltage, strength,
                                             None, None, artificial_source)
        for i in range(1):
            synapse.update(i)
        print(synapse.voltage(), voltage)
        self.assertTrue(synapse.voltage() < voltage)


if __name__ == '__main__':
    unittest.main()
