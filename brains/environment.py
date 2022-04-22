import brains.utils as utils

import string
import random
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass

# fix magic numbers
class STDPTestEnvironment:
    '''
    Very basic environment that only provides input to a brain but ignores output from the brain
    and does not reward it. All environments must implement these functions.
    '''
    def __init__(self, epoch_length=400):
        self._epoch_length = epoch_length

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        is_first_cell = x_grid_position == 0 and y_grid_position == 0
        is_second_cell = x_grid_position == 1 and y_grid_position == 0
        if step % self._epoch_length == 0 and step > 0 and is_first_cell :
            return 0.1
        if step % self._epoch_length == 10 and step > 0 and is_second_cell :
            return 0.1
        return 0

    def active(self, step):
        first_cell_time = step % self._epoch_length == 0 and step > 0
        second_cell_time =step % self._epoch_length == 10 and step > 0
        return first_cell_time or  second_cell_time

    def has_reward(self):
        return False

    def step(self, step):
        pass

    def accept_fire(self, step, x_grid_position, y_grid_position):
        pass

@dataclass
class ResultTracker:
    win: int = 0
    loss: int = 0
    none_fired: int = 0
    all_fired: int = 0
    indeterminate: int = 0
    win: int = 0
    epochs: int = 0

    def update(self, correct_cell_fired, incorrect_cell_fired):
        self.epochs += 1
        if correct_cell_fired and not incorrect_cell_fired:
            self.win += 1
        elif not correct_cell_fired and not incorrect_cell_fired:
            self.none_fired += 1
            self.indeterminate += 1
        elif correct_cell_fired and incorrect_cell_fired:
            self.all_fired += 1
            self.indeterminate += 1
        elif not correct_cell_fired and incorrect_cell_fired:
            self.loss += 1

class BaseEpochChallengeEnvironment:
    '''
    User is expected to implement:
    potential_from_location to act as input from the environment to the brain.
    accept_fire to handle output from the brain to determine if the brain has fired the right cell.

    Class handles rewarding at the right time assuming that the correct output cell and only the
    current output cell must fire by half way through the epoch and that after that a reward should
    be given to the brain exactly one time.
    '''
    def __init__(self, epoch_length, input_delay):
        self._epoch_length = epoch_length
        self._input_delay = input_delay

        self._success = False
        self._reward_provided = False
        self._correct_cell_fired = False
        self._incorrect_cell_fired = False

        self._result_tracker = ResultTracker()
        
    def active(self, step):
        real_step = step - self._input_delay
        return real_step % self._epoch_length == 0 and step > real_step

    def step(self, step):
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            print(self._result_tracker)
            self._correct_cell_fired = False
            self._incorrect_cell_fired = False
            self._reward_provided = False
            self._success = False
        elif real_step % self._epoch_length == self._epoch_length//2:
            self._result_tracker.update(self._correct_cell_fired, self._incorrect_cell_fired)
            if self._correct_cell_fired and not self._incorrect_cell_fired:
                self._success = True
            else:
                self._success = False

    def has_reward(self):
        if self._success and not self._reward_provided:
            self._reward_provided = True
            return True
        return False

class EasyEnvironment(BaseEpochChallengeEnvironment):
    '''
    Designed for easy leaning

    Randomly chooses to spike one of two input cells each epoch. If the corresponding output cell
    fires the brain is rewarded. Also spikes a third input cell randomly that is unrelated to what
    output cell is rewarded.
    '''
    def __init__(self, epoch_length, input_delay):
        super().__init__(epoch_length, input_delay)
        self._zero_stage = True
        self._one_stage = False
        self._fire_the_random_input_cell = False

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and step > real_step
        is_input_cell = x_grid_position == 0 or x_grid_position == 3
        if  is_correct_time and is_input_cell:
            if y_grid_position == 0 and self._zero_stage:
                return 0.3
            if y_grid_position == 1 and self._one_stage:
                return 0.3
            if y_grid_position == 2 and self._fire_the_random_input_cell:
                return 0.3
        return 0.0

    def step(self, step):
        super().step(step)
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._fire_the_random_input_cell = random.random() > 0.5
            if random.random() > 0.5:
                self._one_stage = False
                self._zero_stage = True
            else:
                self._zero_stage = False
                self._one_stage = True

    # should just take layer id
    def accept_fire(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        if step <= real_step:
            return

        if x_grid_position != 9:
            return

        if y_grid_position == 0 and self._zero_stage or y_grid_position == 1 and self._one_stage:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True
    
class TestEnvironment(BaseEpochChallengeEnvironment):
    def __init__(self, input_points, reward_points, epoch_length, input_delay=0):
        super().__init__(epoch_length, input_delay)
        
        self.input_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for (step, x, y, strength) in input_points:
            self.input_dict[step][x][y] = strength

        # List of corrdinates or Nones specifying a reward for a given epoch
        self._reward_points = reward_points
        self._reward_point = self._reward_points[0]

    def active(self, step):
        return step in self.input_dict

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        return self.input_dict[step][x_grid_position][y_grid_position]

    def step(self, step):
        super().step(step)
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._reward_point = self._reward_points[real_step//self._epoch_length]

    def accept_fire(self, step, x_grid_position, y_grid_position):
        if self._reward_point is None:
            return

        if x_grid_position == self._reward_point[0] and y_grid_position == self._reward_point[1]:
            self._correct_cell_fired = True


class HandwritenEnvironment(BaseEpochChallengeEnvironment):
    def __init__(self, input_delay=None, epoch_length=None,
                 image_lines=None, shuffle=False,
                 last_layer_x_grid_position=None, file_name=None):
        super().__init__(epoch_length, input_delay)

        self._image_width = None
        self._last_layer_x_grid_position = last_layer_x_grid_position
        if (image_lines is None and file_name is None) or (image_lines and file_name):
            raise Exception("HandwrittenEnvironment contructor requires either a file_name or image_lines but not both")
        
        if image_lines is None:
            image_lines = self._get_image_lines_from_file(file_name)
        wanted_letters = ['o', 'x']
        self._images = self._load_handwriting(image_lines, wanted_letters, shuffle)
        self._letter_id_by_letter = {'o': 0, 'x': 1}
        self._letter_by_letter_id = {0: '0', 1: 'x'}

    def accept_fire(self, step, x_grid_position, y_grid_position):
        real_step = step - self._input_delay
        (letter, _) = self._images[(real_step//self._epoch_length) - 1]
        if step <= real_step:
            return

        if x_grid_position != self._last_layer_x_grid_position:
            return

        if y_grid_position == self._letter_id_by_letter[letter]:
            print(self._letter_by_letter_id[y_grid_position], "fired")
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True
            
    # so many magic numbers
    # also so many errors possilbe
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        # bad names
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and step > real_step

        if x_grid_position >= self._image_width  and x_grid_position < (self._image_width * 2) + 1:
            x_grid_position = x_grid_position - self._image_width - 1
            
        
        is_input_cell = x_grid_position < self._image_width
        if  is_correct_time and is_input_cell:
            image_index = real_step//self._epoch_length - 1
            if image_index >= len(self._images):
                #print("ran out of images to show network will continue running with no inputs")
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
        

    def _load_handwriting(self, lines, wanted_letters, shuffle):
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

        images = []
        for letter, images_for_letter in images_by_letter.items():
            if letter in  wanted_letters:
                for image in images_for_letter:
                    images.append((letter, image,))
        if shuffle:
            random.shuffle(images)
        return images

def data_dir_file_path(file_name):
    base_path = Path(__file__).parent / "data"
    file_path = (base_path / file_name).resolve()
    return file_path

def shorten_file():
    input_file = open(data_dir_file_path("A_Z Handwritten Data.csv"))
    output_file = open(data_dir_file_path("o_x_hand_written_all.csv"), 'w')

    wanted_images_per_letter = 5000
    wanted_letters = ['o', 'x']
    letter_counts = {'o': 0, 'x': 0}
    for line in input_file:
        cells = line.split(",")
        alphabet = list(string.ascii_lowercase)
        letter = alphabet[int(cells[0])]
        if letter in wanted_letters:
            if letter_counts[letter] > wanted_images_per_letter:
                continue
            output_file.write(line)
            letter_counts[letter] += 1
    print(letter_counts)

if __name__ == '__main__':
    # read_handwriting()
    shorten_file()

    
