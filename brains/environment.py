import brains.utils as utils

import string
import random
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass

class STDPTestEnvironment:
    '''
    Very basic environment that provides input to a brain but ignores output from the brain
    and does not reward the brain. Input is provided to 2 cells every epoch with a 10 step
    delay between the when the cells get input.
    '''
    def __init__(self, epoch_length=400, input_delay=50):
        self._epoch_length = epoch_length
        self._input_delay = input_delay
        self._second_input_spike_delay = 10

    def stimuli(self, step):
        real_step = step - self._input_delay
        if real_step < 0:
            return set()

        if real_step % self._epoch_length == 0:
            return {(0, 0, 0.1,)}
        if real_step % self._epoch_length == self._second_input_spike_delay:
            return {(1, 0, 0.1,)}
        return set()

    def active(self, step):
        real_step = step - self._input_delay
        first_cell_time = real_step % self._epoch_length == 0
        second_cell_time = real_step % self._epoch_length == self._second_input_spike_delay
        return first_cell_time or  second_cell_time

    def has_reward(self):
        return False

    def step(self, step):
        pass

    def accept_fire(self, step, output_id):
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
    stimuli to act as input from the environment to the brain.
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

    def stimuli(self, step):
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and step > real_step
        if not is_correct_time:
            return set()

        stimuli = set()
        if self._zero_stage:
            stimuli.add((0, 0, 0.3,))
        if self._one_stage:
            stimuli.add((0, 1, 0.3,))
        if self._fire_the_random_input_cell:
            stimuli.add((0, 2, 0.3,))
        return stimuli

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

    def accept_fire(self, step, output_id):
        real_step = step - self._input_delay
        if step <= real_step:
            return

        if output_id == 0 and self._zero_stage or output_id == 1 and self._one_stage:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True
    
class TestEnvironment(BaseEpochChallengeEnvironment):
    def __init__(self, input_points, reward_ids, epoch_length, input_delay=0):
        super().__init__(epoch_length, input_delay)
        self._stimuli = defaultdict(list)
        for (step, x, y, strength) in input_points:
            self._stimuli[step].append((x, y, strength,))

        # List of corrdinates or Nones specifying a reward for a given epoch
        self._reward_ids = reward_ids
        self._reward_id = self._reward_ids[0]

    def active(self, step):
        return step in self._stimuli

    def stimuli(self, step):
        return self._stimuli[step]

    def step(self, step):
        super().step(step)
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._reward_id = self._reward_ids[real_step//self._epoch_length]

    def accept_fire(self, step, output_id):
        if self._reward_id is None:
            return
        if output_id == self._reward_id:
            self._correct_cell_fired = True


class HandwritenEnvironment(BaseEpochChallengeEnvironment):
    def __init__(self, epoch_length, input_delay, output_id_by_letter,
                 image_lines=None, shuffle=False, file_name=None):
        super().__init__(epoch_length, input_delay)

        self._image_width = None
        if (image_lines is None and file_name is None) or (image_lines and file_name):
            raise Exception("HandwrittenEnvironment contructor requires either a file_name or image_lines but not both")
        
        if image_lines is None:
            image_lines = self._get_image_lines_from_file(file_name)
        
        self._output_id_by_letter = output_id_by_letter
        wanted_letters = sorted(output_id_by_letter.keys())
        self._images = self._load_handwriting(image_lines, wanted_letters, shuffle)
        
    def accept_fire(self, step, output_id):
        real_step = step - self._input_delay
        if real_step//self._epoch_length >= len(self._images):
            return

        if real_step < 0:
            return

        image_index = real_step//self._epoch_length
        (letter, image) = self._images[image_index]

        if output_id == self._output_id_by_letter[letter]:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True

    def stimuli(self, step):
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and real_step >= 0
        if not is_correct_time:
            return set()

        image_index = real_step//self._epoch_length
        if image_index >= len(self._images):
            #print("ran out of images to show network will continue running with no inputs")
            return set()

        stimuli = set()
        (letter, image) = self._images[image_index]
        for i, pixel in enumerate(image):
            if pixel > 50:
                x = i % self._image_width
                y = i // self._image_width
                stimuli.add((x, y, 0.3,))
        return stimuli

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

        letter_image_pairs = []
        for letter in wanted_letters:
            for image in images_by_letter[letter]:
                letter_image_pairs.append((letter, image,))
        if shuffle:
            random.shuffle(letter_image_pairs)
        return letter_image_pairs

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
