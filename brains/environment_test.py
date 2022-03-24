from environment import HandwritenEnvironment
import unittest

class TestBuildingNetwork(unittest.TestCase):
    def test_read_handwritting(self):
        '''
        '''
        # clearly could test better
        # never testing out of bounds
        # never testing other letters
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        delay = 50
        frequency = 150
        environment = HandwritenEnvironment(delay, frequency, image_lines)
        first_image_step = delay + frequency
        third_image_step = delay + frequency * 3
        self.assertEqual(environment.potential_from_location(first_image_step, 0, 0), 0)
        self.assertGreater(environment.potential_from_location(first_image_step, 1, 0), 0)
        self.assertEqual(environment.potential_from_location(first_image_step, 1, 1), 0)

        # Note the image reordering this refers to x
        self.assertGreater(environment.potential_from_location(third_image_step, 1, 1), 0)

if __name__ == '__main__':
    unittest.main()
