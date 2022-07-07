class ParameterTestEnvironment:
    '''
    Very basic environment that provides input to a brain but ignores output from the brain
    and does not reward the brain. Input is provided to 2 cells every epoch with a 10 step
    delay between the when the cells get input.
    '''
    def __init__(self, epoch_length=400, input_delay=50):
        self._epoch_length = epoch_length
        self._input_delay = input_delay

    def stimuli(self, step):
        real_step = step - self._input_delay
        if real_step < 0:
            return set()

        if real_step % self._epoch_length == 0:
            # should not cause spike to propagate
            return {(0, 0, 0.1,)}
            # should cause spike to propagate
            #return {(0, 0, 0.1,) , (0, 1, 0.1,)}
        return set()

    def active(self, step):
        real_step = step - self._input_delay
        return real_step % self._epoch_length == 0

    def has_reward(self):
        return False

    def step(self, step, output_ids):
        pass

    def video_output(self, step):
        return ["answer: none"]
