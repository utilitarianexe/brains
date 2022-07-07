from dataclasses import dataclass
from collections import defaultdict
from abc import ABC, abstractmethod


def result_convert(found_output_ids: list, desired_output_id:int) -> tuple[bool, bool]:
    correct_cell_fired = False
    incorrect_cell_fired = False
    if desired_output_id in found_output_ids:
        correct_cell_fired = True

    for output_id in found_output_ids:
        if output_id != desired_output_id:
            incorrect_cell_fired = True
    return correct_cell_fired, incorrect_cell_fired

@dataclass
class ResultTracker:
    epochs: int = 0
    one_cell_fired: int = 0
    none_fired: int = 0
    at_least_some_fired: int = 0
    total_fires: int = 0
    double_spike: int = 0
    all_fired: int = 0
    null_desired_output: int = 0
    
    one_cell_fired_not_null: int = 0
    rewarded: int = 0
    win: int = 0
    fail: int = 0
    accuracy: float = 0.0


    def update(self, found_output_ids: list, desired_output_id:int, possible_outputs:list, step:int):
        print(f"found: {sorted(found_output_ids)} desired: {desired_output_id}")
        self.epochs += 1

        number_cells_fired = len(set(found_output_ids))
        if number_cells_fired == 1:
            self.one_cell_fired += 1
        if number_cells_fired == 0:
            self.none_fired += 1
        if number_cells_fired > 0:
            self.at_least_some_fired += 1

        self.total_fires += len(found_output_ids)

        if number_cells_fired < len(found_output_ids) - 1:
            self.double_spike += 1
            
        if number_cells_fired == len(possible_outputs) - 1:
            self.all_fired += 1

        if desired_output_id is None:
            self.null_desired_output += 1
            return

        if number_cells_fired == 1:
            self.one_cell_fired_not_null += 1

        if desired_output_id in found_output_ids:
            self.rewarded += 1
            
        correct_cell_fired, incorrect_cell_fired = result_convert(found_output_ids, desired_output_id)
        if correct_cell_fired and not incorrect_cell_fired:
            self.win += 1
        if incorrect_cell_fired and number_cells_fired == 1:
            self.fail += 1

        if self.win + self.fail > 0:
            self.accuracy = float(self.win) / float(self.win + self.fail)


class BaseEpochChallengeEnvironment(ABC):
    '''
    User is expected to implement:
    desired_output_id expected output from brain to determine if the brain has fired the right cell
    stimuli to act as input from the environment to the brain.
    _possible_outputs variable
    See FakeEnvironment for examples

    Class handles rewarding at the right time assuming that the correct output cell and only the
    current output cell must fire by half way through the epoch and that after that a reward should
    be given to the brain exactly one time.
    '''
    def __init__(self, epoch_length: int, input_delay: int):
        self._epoch_length = epoch_length
        self._input_delay = input_delay

        self._success = False
        self._reward_provided = False

        self._found_output_ids: list[int] = []
        self._result_tracker = ResultTracker()
        self._possible_outputs: list[int] = []
        
    def active(self, step: int) -> bool:
        real_step = step - self._input_delay
        return real_step % self._epoch_length == 0 and step > real_step

    @abstractmethod
    def desired_output_id(self, step: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def stimuli(self, step: int) -> list:
        raise NotImplementedError

    def step(self, step: int):
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            print(self._result_tracker)
            self._found_output_ids = []
            self._reward_provided = False
            self._success = False
        elif real_step % self._epoch_length == self._epoch_length//2:
            desired_output_id = self.desired_output_id(step)
            self._result_tracker.update(self._found_output_ids, desired_output_id,
                                        self._possible_outputs, step)
            if self.has_success(desired_output_id):
                self._success = True
            else:
                self._success = False
                
    def has_success(self, desired_output_id: int) -> bool:
        if desired_output_id is None:
            return False
        return desired_output_id in self._found_output_ids

    def video_output(self, step: int) -> list:
        output_id = self.desired_output_id(step)
        if output_id is None:
            return ["expected output: none"]
        return [f"expected output: {output_id}"]

    def has_reward(self) -> bool:
        if self._success and not self._reward_provided:
            self._reward_provided = True
            return True
        return False

    # really output ids should come from step
    # that way model does not need to carry around environment
    def accept_fire(self, step: int, output_id: int):
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

    def active(self, step: int) -> bool:
        return step in self._stimuli

    def stimuli(self, step: int) -> list:
        return self._stimuli[step]

    def step(self, step: int):
        super().step(step)
        real_step = step - self._input_delay
        if real_step % self._epoch_length == 0:
            self._reward_id = self._reward_ids[real_step//self._epoch_length]

    def desired_output_id(self, step):
        return self._reward_id
