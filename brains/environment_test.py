from brains.environment import HandwritenEnvironment
import unittest

class TestBuildingNetwork(unittest.TestCase):
    def test_read_handwritting(self):
        '''
        '''
        # clearly could test better
        # never testing out of bounds
        # never testing other letters

        # Format is letter then voltages a line is one image
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        delay = 50
        frequency = 150
        environment = HandwritenEnvironment(delay, frequency, image_lines)
        first_image_step = delay + frequency
        third_image_step = delay + frequency * 3
        self.assertEqual(environment.stimuli(first_image_step), {(1, 0, 0.3), (0, 1, 0.3)})
        
        # Note the image reordering this refers to x(letter 23) when not shuffled images are
        # presented in alphabetical order.
        self.assertEqual(environment.stimuli(third_image_step), {(1, 0, 0.3), (0, 1, 0.3), (1, 1, 0.3)})

    def test_reward(self):
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        delay = 50
        frequency = 500
        environment = HandwritenEnvironment(delay, frequency, image_lines,
                                            last_layer_x_grid_position = 3)
        first_image_step = delay + frequency
        third_image_step = delay + frequency * 3

        for i in range(2000):
            environment.step(i)
            if i == first_image_step + 20:
                environment.accept_fire(i, 3, 0)
            if i == first_image_step + 260:
                self.assertTrue(environment.has_reward())
            if i == first_image_step + 300:
                self.assertFalse(environment.has_reward())
            if i == third_image_step:
                self.assertFalse(environment.has_reward())

if __name__ == '__main__':
    unittest.main()
