from collections import defaultdict
import string
from enum import Enum

#also named bad
# maybe not used
class EnvironmentType(Enum):
    SIMPLE = 1
    HANDWRITING = 2

# no variables needed but still use self for consistancy
class SimpleEnvironment:
    def __init__(self):
        pass

    def potential_from_location(self, step, x_grid_position, y_grid_position):
        if step % 50000 == 200 and step > 0 and x_grid_position == 0 and y_grid_position == 0:
            return 0.15
        return 0

class HandwritenEnvironment:
    def __init__(self, image_lines=None):
        if image_lines is None:
            image_lines = self._get_image_lines_from_file()
        self._images_by_letter = self._load_handwriting(image_lines)
        
    # so many magic numbers
    # also so many errors possilbe
    def potential_from_location(self, step, x_grid_position, y_grid_position):
        delay = 50
        # bad names
        real_step = step - delay
        frequency = 200
        if real_step % frequency == 0 and step > real_step and x_grid_position < 28:
            images_for_a = self._images_by_letter['a']
            image_for_a = images_for_a[(real_step//200) - 1]
            pixel_position = y_grid_position * 28 + x_grid_position
            pixel = image_for_a[pixel_position]
            if pixel > 50:
                return 0.15
        return 0

    def _get_image_lines_from_file(self):
        # magic file name
        # not checking exceptions
        # wrong place for this function
        return open("a_hand_written_short.csv")
        

    def _load_handwriting(self, lines):
        alphabet = list(string.ascii_lowercase)
        images_by_letter = defaultdict(list)
        for line in lines:
            cells = line.split(",")
            if cells[-1][-1] == '\n':
                cells[-1] = cells[-1][:-1]
            cells = [int(cell) for cell in cells if cell ]
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

# if __name__ == '__main__':
#     read_handwriting()
#     shorten_file()

    
