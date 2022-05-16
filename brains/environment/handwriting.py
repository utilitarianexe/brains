import brains.utils as utils
import brains.environment.base as base

import string
import random
from collections import defaultdict

class HandwritingEnvironment(base.BaseEpochChallengeEnvironment):
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

    def _get_image_lines_from_file(self, file_name):
        file_path = utils.data_dir_file_path(file_name)
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

def shorten_file():
    input_file = open(utils.data_dir_file_path("A_Z Handwritten Data.csv"))
    output_file = open(utils.data_dir_file_path("o_x_hand_written_all.csv"), 'w')

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
