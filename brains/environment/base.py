from dataclasses import dataclass
from collections import defaultdict

def result_convert(found_output_ids, desired_output_id):
    correct_cell_fired = False
    incorrect_cell_fired = False
    if desired_output_id in found_output_ids:
        correct_cell_fired = True

    for out_id in found_output_ids:
        if out_id != desired_output_id:
            incorrect_cell_fired = True
    return correct_cell_fired, incorrect_cell_fired

@dataclass
class ResultTracker:
    win: int = 0
    loss: int = 0
    none_fired: int = 0
    all_fired: int = 0
    indeterminate: int = 0
    rewarded: int = 0
    epochs: int = 0

    def update(self, found_output_ids, desired_output_id, possible_outputs):
        #print(f"found: {found_output_ids} desired: {desired_output_id}")
        self.epochs += 1
        if desired_output_id in found_output_ids:
            self.rewarded += 1
        
        correct_cell_fired, incorrect_cell_fired = result_convert(found_output_ids, desired_output_id)
        if correct_cell_fired and not incorrect_cell_fired:
            self.win += 1
        if not correct_cell_fired and incorrect_cell_fired:
            self.loss += 1

        # I guess technically these could be wins and losses
        if len(found_output_ids) == 0:
            self.none_fired += 1
            self.indeterminate += 1
        if len(found_output_ids) == len(possible_outputs):
            self.all_fired += 1
            self.indeterminate += 1

class BaseEpochChallengeEnvironment:
    '''
    User is expected to implement:
    stimuli to act as input from the environment to the brain.
    desired_output expected output from brain to determine if the brain has fired the right cell
    _possible_outputs variable
    See FakeEnvironment for examples

    Class handles rewarding at the right time assuming that the correct output cell and only the
    current output cell must fire by half way through the epoch and that after that a reward should
    be given to the brain exactly one time.
    '''
    def __init__(self, epoch_length, input_delay):
        self._epoch_length = epoch_length
        self._input_delay = input_delay

        self._success = False
        self._reward_provided = False

        self._found_output_ids = []
        self._result_tracker = ResultTracker()
        self._possible_outputs = []
        
    def active(self, step):
        real_step = step - self._input_delay
        return real_step % self._epoch_length == 0 and step > real_step

    def step(self, step):
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            print(self._result_tracker)
            self._found_output_ids = []
            self._reward_provided = False
            self._success = False
        elif real_step % self._epoch_length == self._epoch_length//2:
            desired_output_id = self.desired_output_id(step)
            self._result_tracker.update(self._found_output_ids, desired_output_id,
                                        self._possible_outputs)
            if self.has_success(desired_output_id):
                self._success = True
            else:
                self._success = False
                
    def has_success(self, desired_output_id):
        #return desired_output_id in self._found_output_ids
        correct_cell_fired, incorrect_cell_fired = result_convert(self._found_output_ids,
                                                                  desired_output_id)
        return correct_cell_fired and not incorrect_cell_fired
        

    def video_output(self, step):
        output_id = self.desired_output_id(step)
        if output_id is None:
            return ["expected output: none"]
        return [f"expected output: {output_id}"]

    def has_reward(self):
        if self._success and not self._reward_provided:
            self._reward_provided = True
            return True
        return False

    # really output ids should come from step
    # that way model does not need to carry around environment
    def accept_fire(self, step, output_id):
        self._found_output_ids.append(output_id)


class FakeEnvironment(BaseEpochChallengeEnvironment):
    def __init__(self, input_points, reward_ids, epoch_length, input_delay=0):
        super().__init__(epoch_length, input_delay)
        self._possible_outputs = set(reward_ids)
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

    def desired_output_id(self, step):
        return self._reward_id
