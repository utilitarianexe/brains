from environment import HandwritenEnvironment
import unittest


class TestBuildingNetwork(unittest.TestCase):
    def test_read_handwritting(self):
        '''
        '''
        # clearly could test better
        # never testing y
        # never testing out of bounds x
        # never testing other letters
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        environment = HandwritenEnvironment(image_lines)
        self.assertEqual(environment.potential_from_location(250, 0, 0), 0)
        self.assertGreater(environment.potential_from_location(250, 1, 0), 0)
        self.assertEqual(environment.potential_from_location(250, 3, 0), 0)
        self.assertGreater(environment.potential_from_location(650, 3, 0), 0)

if __name__ == '__main__':
    unittest.main()
