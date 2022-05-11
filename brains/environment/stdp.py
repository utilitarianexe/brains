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
