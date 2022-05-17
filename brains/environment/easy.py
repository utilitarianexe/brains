import brains.environment.base as base

import random

class EasyEnvironment(base.BaseEpochChallengeEnvironment):
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

    def desired_output_id(self, step):
        real_step = step - self._input_delay
        if step <= real_step:
            return None

        if self._zero_stage:
            return 0
        else:
            return 1
