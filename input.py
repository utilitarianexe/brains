from collections import defaultdict
import string
from enum import Enum

# this file is named badly because of keywork overlap

#also named bad
class InputType(Enum):
     SIMPLE = 1
     HANDWRITING = 2

class Input:
    def __init__(self, inputs, answers):
        self.inputs = inputs
        self.answers = answers

# also this still feels like functional overkill
# these grid positions are weird
def fake_input_simple(step, x_grid_position, y_grid_position):
    if step % 50000 == 200 and step > 0 and x_grid_position == 0 and y_grid_position == 0:
        return 0.15
    return 0

# so many magic numbers
# also so many errors possilbe
def handwritten_letters_helper(step, x_grid_position, y_grid_position, images_by_letter):
    delay = 50
    # bad names
    real_step = step - delay
    frequency = 200
    if real_step % frequency == 0 and step > real_step:
        images_for_a = images_by_letter['a']
        image_for_a = images_for_a[real_step//150]
        pixel_position = y_grid_position * 28 + x_grid_position
        pixel = image_for_a[pixel_position]
        if pixel > 50:
            return 0.15
    return 0

# wow this is stupidly complex as cool as it is
def handwritten_letters_func():
    images_by_letter = read_handwriting()
    def func(step, x_grid_position, y_grid_position):
        return handwritten_letters_helper(step, x_grid_position, y_grid_position, images_by_letter)
    return func


# need validation and tests
def read_handwriting():
    f = open("a_hand_written_short.csv")
    alphabet = list(string.ascii_lowercase)
    images_by_letter = defaultdict(list)
    for line in f:
        cells = line.split(",")
        
        # strip ending new line
        if cells[-1][-1] == '\n':
            cells[-1] = cells[-1][:-1]
        cells = [int(cell) for cell in cells]
        image = cells[1:]
        letter = alphabet[cells[0]]
        images_by_letter[letter].append(image)
        if letter != 'a':
            break
    return images_by_letter

def shorten_file():
    i = open("A_Z Handwritten Data.csv")
    o = open("a_hand_written_short.csv", 'w')
    for line_number, line in enumerate(i):
        o.write(line)
        if line_number > 10:
            break


if __name__ == '__main__':
    read_handwriting()
    # shorten_file()

    
