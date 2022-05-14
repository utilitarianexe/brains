from dataclasses import dataclass
from collections import defaultdict

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

class FakeEnvironment(BaseEpochChallengeEnvironment):
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
