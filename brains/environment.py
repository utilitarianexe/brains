import brains.utils as utils

import string
import random
from collections import defaultdict
from pathlib import Path

class TestEnvironment:
    def __init__(self, input_points, reward_ranges):
        self.input_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for (step, x, y, strength) in input_points:
            self.input_dict[step][x][y] = strength
        self.reward_dict = defaultdict(lambda: defaultdict(list))
        for (x, y, step_range) in reward_ranges:
            self.reward_dict[x][y].append(step_range)

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        return self.input_dict[step][x_grid_position][y_grid_position]
    
    def reward(self, step, x_grid, y_grid):
        reward_ranges = self.reward_dict[x_grid][y_grid]
        for (start, end,) in reward_ranges:
            if step > start and step < end:
                return True
        return False

class STDPTestEnvironment:
    def __init__(self):
        pass

    # need to put these magics in default run
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        frequency = 500
        if step % frequency == 10 and step > 0 and (x_grid_position == 1 and y_grid_position == 0) :
            return 0.1
        
        if step % frequency == 0 and step > 0 and (x_grid_position == 0 and y_grid_position == 0) :
            return 0.1
        return 0

    def reward(self, step, x_grid, y_grid):
        return False


class HandwritenEnvironment:
    def __init__(self, delay=None, frequency=None, image_lines=None, shuffle=False,
                 last_layer_x_grid_position=None):
        self._delay = delay
        self._frequency = frequency
        self._image_width = None
        self._last_layer_x_grid_position = last_layer_x_grid_position
        
        if image_lines is None:
            image_lines = self._get_image_lines_from_file()
        images_by_letter = self._load_handwriting(image_lines)
        x_images = images_by_letter['x']
        o_images = images_by_letter['o']
        self._images = []
        for image in o_images:
            self._images.append(('o', image,))
        for image in x_images:
            self._images.append(('x', image,))

        # not sure this is best place to do this
        if shuffle:
            random.shuffle(self._images)
        self._letter_id_by_letter = {'o': 0, 'x': 1}

    # check this
    def reward(self, step, x_grid, y_grid):
        if x_grid != self._last_layer_x_grid_position:
            return False
        real_step = step - self._delay
        (letter, _) = self._images[(real_step//self._frequency) - 1]
        if step > real_step:
            return y_grid == self._letter_id_by_letter[letter]
        return False
        
    # so many magic numbers
    # also so many errors possilbe
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        # bad names
        real_step = step - self._delay
        is_correct_time = real_step % self._frequency == 0 and step > real_step
        is_input_cell = x_grid_position < self._image_width
        if  is_correct_time and is_input_cell:
            image_index = (real_step//self._frequency) - 1
            (_, image) = self._images[image_index]
            pixel_position = y_grid_position * self._image_width + x_grid_position
            pixel = image[pixel_position]
            if pixel > 50:
                return 0.3
        return 0

    def _get_image_lines_from_file(self):
        # magic file name
        # not checking exceptions
        # wrong place for this function
        base_path = Path(__file__).parent
        file_path = (base_path / "./data/o_x_hand_written_short.csv").resolve()
        return open(file_path)
        

    def _load_handwriting(self, lines):
        alphabet = list(string.ascii_lowercase)
        images_by_letter = defaultdict(list)
        for line in lines:
            cells = line.split(",")
            if cells[-1][-1] == '\n':
                cells[-1] = cells[-1][:-1]
            cells = [int(cell) for cell in cells if cell ]
            image = cells[1:]
            if self._image_width is None:
                self._image_width = utils.newtons_square_root(len(image))
            if self._image_width**2 != len(image):
                # need to look up how exceptions work
                raise Exception("bad image size", len(image))
                
            letter = alphabet[cells[0]]
            images_by_letter[letter].append(image)
        return images_by_letter

def shorten_file():
    input_file = open("A_Z Handwritten Data.csv")
    output_file = open("o_x_hand_written_short.csv", 'w')
    wanted_images_per_letter = 10
    wanted_letters = ['o', 'x']
    current_letter_index = 0
    current_letter_count = 0
    for line in input_file:
        cells = line.split(",")
        alphabet = list(string.ascii_lowercase)
        letter = alphabet[int(cells[0])]
        wanted_letter = wanted_letters[current_letter_index]
        if letter == wanted_letter:
            output_file.write(line)
            current_letter_count += 1
            if current_letter_count == wanted_images_per_letter - 1:
                current_letter_count = 0
                current_letter_index += 1
                if current_letter_index == len(wanted_letters):
                    break

if __name__ == '__main__':
    # read_handwriting()
    shorten_file()

    
