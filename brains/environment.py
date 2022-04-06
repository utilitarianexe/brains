import brains.utils as utils

import string
import random
from collections import defaultdict
from pathlib import Path

class EasyEnvironment:
    '''
    Designed for easy leaning
    '''
    def __init__(self, epoch_length, input_delay):
        self._epoch_length = epoch_length

        self._reward = False
        self._rewarded = False
        self._correct_cell_fired = False
        self._incorrect_cell_fired = False
        self._input_delay = input_delay
        self._zero_stage = True
        self._one_stage = False

        self._win = 0
        self._loss = 0
        self._none_fired = 0
        self._all_fired = 0
        self._indeterminate = 0
        self._epochs = 0

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and step > real_step
        is_input_cell = x_grid_position == 0
        if  is_correct_time and is_input_cell:
            if y_grid_position == 0 and self._zero_stage:
                return 0.3
            if y_grid_position == 1 and self._one_stage:
                return 0.3
            if y_grid_position == 2 and random.random() > 0.5:
                return 0.3
        return 0.0

    def step(self, step):
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._epochs += 1
            print("resetting env state")
            print("epochs", self._epochs, "loss", self._loss, "win", self._win, "none_fired", self._none_fired, "all_fired", self._all_fired, "indeterminate", self._indeterminate)
            self._correct_cell_fired = False
            self._incorrect_cell_fired = False
            self._rewarded = False
            self._reward = False
            if random.random() > 0.5:
                self._one_stage = False
                self._zero_stage = True
                return
            if self._zero_stage:
                self._zero_stage = False
                self._one_stage = True
                return
                
        elif real_step % (self._epoch_length//2) == 0:
            if self._correct_cell_fired and not self._incorrect_cell_fired:
                self._win += 1
                self._reward = True
            elif not self._correct_cell_fired and not self._incorrect_cell_fired:
                self._none_fired += 1
                self._indeterminate += 1
                self._reward = False
            elif self._correct_cell_fired and self._incorrect_cell_fired:
                self._all_fired += 1
                self._indeterminate += 1
                self._reward = False
            elif not self._correct_cell_fired and self._incorrect_cell_fired:
                self._loss += 1
                self._reward = False

    # should just take layer id
    def accept_fire(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        if step <= real_step:
            return

        if x_grid_position != 6:
            return

        if y_grid_position == 0 and self._zero_stage or y_grid_position == 1 and self._one_stage:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True
    
    def has_reward(self):
        if self._reward and not self._rewarded:
            self._rewarded = True
            return True
        return False

class TestEnvironment:
    def __init__(self, input_points, reward_points, reward_frequency):
        self._reward_frequency = reward_frequency
        
        self.input_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for (step, x, y, strength) in input_points:
            self.input_dict[step][x][y] = strength

        # List of corrdinates or Nones specifying a reward for a given epoch
        self._reward_points = reward_points
        self._reward = False
        self._reward_point = self._reward_points[0]

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        return self.input_dict[step][x_grid_position][y_grid_position]

    def step(self, step):
        if step % self._reward_frequency == 0:
            self._reward = False
            self._reward_point = self._reward_points[step//self._reward_frequency]

    def accept_fire(self, step, x_grid_position, y_grid_position):
        if self._reward_point is None:
            return

        if x_grid_position == self._reward_point[0] and y_grid_position == self._reward_point[1]:
            self._reward = True
    
    def has_reward(self):
        return self._reward

class STDPTestEnvironment:
    def __init__(self, epoch_length=300):
        self._epoch_length = epoch_length

    # fix magic numbers
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        is_first_cell = x_grid_position == 0 and y_grid_position == 0
        is_second_cell = x_grid_position == 1 and y_grid_position == 0
        if step % self._epoch_length == 0 and step > 0 and is_first_cell :
            return 0.1
        if step % self._epoch_length == 10 and step > 0 and is_second_cell :
            return 0.1
        return 0

    def has_reward(self):
        return False

    def step(self, step):
        pass

    def accept_fire(self, step, x_grid_position, y_grid_position):
        pass


class HandwritenEnvironment:
    def __init__(self, input_delay=None, epoch_length=None, image_lines=None, shuffle=False,
                 last_layer_x_grid_position=None, file_name=None):
        print(file_name)

        self._input_delay = input_delay
        self._epoch_length = epoch_length
        self._image_width = None
        self._last_layer_x_grid_position = last_layer_x_grid_position
        
        self._win = 0
        self._loss = 0
        self._none_fired = 0
        self._all_fired = 0
        self._indeterminate = 0
        self._epochs = 0

        self._reward = False
        self._correct_cell_fired = False
        self._incorrect_cell_fired = False
        self._rewarded = False

        if (image_lines is None and file_name is None) or (image_lines and file_name):
            raise Exception("HandwrittenEnvironment contructor requires either a file_name or image_lines but not both")
        
        if image_lines is None:
            image_lines = self._get_image_lines_from_file(file_name)
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

    def step(self, step):
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._epochs += 1
            print("resetting env state")
            print("epochs", self._epochs, "loss", self._loss, "win", self._win, "none_fired", self._none_fired, "all_fired", self._all_fired, "indeterminate", self._indeterminate)
            self._correct_cell_fired = False
            self._incorrect_cell_fired = False
            self._rewarded = False
            self._reward = False
        elif real_step % (self._epoch_length//2) == 0:
            print("env in output state")
            if self._correct_cell_fired and not self._incorrect_cell_fired:
                self._win += 1
                self._reward = True
            elif not self._correct_cell_fired and not self._incorrect_cell_fired:
                self._none_fired += 1
                self._indeterminate += 1
                self._reward = False
            elif self._correct_cell_fired and self._incorrect_cell_fired:
                self._all_fired += 1
                self._indeterminate += 1
                self._reward = False
            elif not self._correct_cell_fired and self._incorrect_cell_fired:
                self._loss += 1
                self._reward = False

    def has_reward(self):
        if self._reward and not self._rewarded:
            self._rewarded = True
            return True
        return False

    def accept_fire(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        (letter, _) = self._images[(real_step//self._epoch_length) - 1]
        if step <= real_step:
            return

        if x_grid_position != self._last_layer_x_grid_position:
            return

        if y_grid_position == self._letter_id_by_letter[letter]:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True
        
    # so many magic numbers
    # also so many errors possilbe
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        # bad names
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and step > real_step
        is_input_cell = x_grid_position < self._image_width
        if  is_correct_time and is_input_cell:
            image_index = real_step//self._epoch_length - 1
            if image_index >= len(self._images):
                print("ran out of images to show network will continue running with no inputs")
                return 0.0

            (_, image) = self._images[image_index]
            pixel_position = y_grid_position * self._image_width + x_grid_position
            pixel = image[pixel_position]
            if pixel > 50:
                return 0.3
        return 0.0

    def _get_image_lines_from_file(self, file_path):
        # magic file name
        # not checking exceptions
        # wrong place for this function
        base_path = Path(__file__).parent / "data"
        file_path = (base_path / file_path).resolve()
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
    input_file = open("./data/A_Z Handwritten Data.csv")
    output_file = open("./data/o_x_hand_written_long.csv", 'w')
    wanted_images_per_letter = 1000
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

    
