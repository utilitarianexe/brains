import brains.utils as utils
import brains.environment.base as base

from collections import defaultdict
import random

# copy paste of handwriting
# magic numbers
class MnistEnvironment(base.BaseEpochChallengeEnvironment):
    def __init__(self, epoch_length, input_delay=0, shuffle=True):
        super().__init__(epoch_length, input_delay)
        images_by_label = read_mnist()
        self._image_width = 28
        self._digits_and_images = []
        for digit, images in images_by_label.items():
            for image in images:
                self._digits_and_images.append((digit, image,))
            
        if shuffle:
            random.shuffle(self._digits_and_images)

    def stimuli(self, step):
        real_step = step - self._input_delay
        is_correct_time = real_step % self._epoch_length == 0 and real_step >= 0
        if not is_correct_time:
            return set()

        image_index = real_step//self._epoch_length
        if image_index >= len(self._digits_and_images):
            #print("ran out of images to show network will continue running with no inputs")
            return set()

        stimuli = set()
        (digit, image) = self._digits_and_images[image_index]
        for i, pixel in enumerate(image):
            if pixel > 50:
                x = i % self._image_width
                y = i // self._image_width
                stimuli.add((x, y, 0.3,))
        return stimuli


    def accept_fire(self, step, output_id):
        real_step = step - self._input_delay
        if real_step//self._epoch_length >= len(self._digits_and_images):
            return

        if real_step < 0:
            return

        image_index = real_step//self._epoch_length
        (digit, image) = self._digits_and_images[image_index]

        if output_id == digit:
            self._correct_cell_fired = True
        else:
            self._incorrect_cell_fired = True

def read(image_file_name, label_file_name, number_of_images_to_read):
    label_file = open(utils.data_dir_file_path(label_file_name), "rb")
    image_file = open(utils.data_dir_file_path(image_file_name), "rb")

    # discard headers
    image_file.read(16)   
    label_file.read(8)

    images_by_label = defaultdict(list)
    for _ in range(number_of_images_to_read):
        label = ord(label_file.read(1))
        image = []
        for _ in range(784):
            value = ord(image_file.read(1))
            image.append(value)
        images_by_label[label].append(image)
    image_file.close()
    label_file.close()
    return images_by_label

def read_mnist():
    return read("train-images.idx3-ubyte", "train-labels.idx1-ubyte", 10000)

if __name__ == '__main__':
    images_by_label = read_mnist()
    print(images_by_label.keys())
    print(images_by_label[0])
