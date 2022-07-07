from brains.environment.handwriting import HandwritingEnvironment
import unittest

class TestHandwriting(unittest.TestCase):
    def test_read_handwriting(self):
        '''
        '''
        # Each string is a letter and one image.
        # 14 represents 'o' 23 represents 'x'. 51 and 0 are intensities of pixels.
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        delay = 50
        frequency = 150
        environment = HandwritingEnvironment(frequency, delay, {'o': 0, 'x': 1},
                                            image_lines=image_lines, shuffle=False)

        # When not shuffled images are shown is alphabetical order.
        first_image_step = delay
        third_image_step = delay + frequency * 2
        self.assertEqual(environment.stimuli(first_image_step), {(1, 0, 0.3), (0, 1, 0.3)})
        self.assertEqual(environment.stimuli(third_image_step), {(1, 0, 0.3), (0, 1, 0.3), (1, 1, 0.3)})

    def test_reward(self):
        # See comments in test_read_handwriting
        image_lines = ['14,0,51,51,0,\n',
                       '23,0,51,51,51\n',
                       '14,0,51,0,51']
        delay = 50
        frequency = 400
        environment = HandwritingEnvironment(frequency, delay, {'o': 0, 'x': 1},
                                            image_lines=image_lines, shuffle=False)
        first_image_step = delay
        third_image_step = delay + frequency * 2

        for i in range(2000):
            output_ids = []
            if i == first_image_step + 20:
                output_ids = [0]
            if i == first_image_step + 30:
                # not enough time has passed
                self.assertFalse(environment.has_reward())
            if i == first_image_step + 210:
                self.assertTrue(environment.has_reward())
            if i == first_image_step + 300:
                # already accepted reward
                self.assertFalse(environment.has_reward())
            if i == third_image_step + 20:
                # wrong cell fires
                output_ids = [0]
                self.assertFalse(environment.has_reward())
            if i == third_image_step + 210:
                # no reward even after enough time because wrong cell fired.
                self.assertFalse(environment.has_reward())
            environment.step(i, output_ids)

if __name__ == '__main__':
    unittest.main()
