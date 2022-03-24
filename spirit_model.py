##### from paper
# each if should be a function name.
# map to variables in paper
# map to ~ chemical channels
# why do we use I for slow potential if that is current(I guess leak current is a potential?). The old paper just calls it y.
# is what I think slow potential really a potential. I it summed with the fast one?
# spikes are single points
# should produce bursts of spikes with the right parameters
# wtf should the ranges be
class SpiritModel():
    def __init__(self, input_decay, alpha, mu, sigma, sigma_next, fake_input):
        self.name = "Spirit Model"
        self.labels = ["~potential", "~input synapse current"]
        self._input_decay = input_decay
        self._alpha = alpha
        self._mu = mu
        self._sigma = sigma
        self._sigma_next = sigma_next
        self._input = 0 # will become array? well many cells anyway.

        self._fast_potential = -0.5
        self._fast_potential_previous = -0.5
        self._slow_potential = -0.5
        self._step_size = 1 #?
        self._fake_input = fake_input

    #acutally should take u as input which is slow_potential + input
    def _next_fast_potential(self, fast_potential, previous_fast_potential, slow_potential, u):
        # if you are under 0 increase. Slower the more negative you start.
        if fast_potential <= 0:
            return self._alpha/(1 - fast_potential)  + u

        #spike if you are over 0 to some set point. but don't if you are already spiked. Should I use u here
        if fast_potential > 0 and fast_potential < self._alpha + slow_potential and previous_fast_potential <= 0: #why previous?
            return self._alpha + slow_potential

        # if you spike fall back on the next step
        if self._alpha + slow_potential <= fast_potential or previous_fast_potential > 0:
            return -1
        print("fail") # make an exception
        return 0

    # mu should be low to make this change slowly    
    def _next_slow_potential(self, fast_potential, slow_potential):
        return slow_potential - self._mu*(fast_potential + 1) + self._mu*self._sigma + self._mu*self._sigma_next # wtf do we have sigma and sigma next

    def _update_voltage(self):
        self._fast_potential = self._next_fast_potential(self._fast_potential, self._fast_potential_previous, self._slow_potential, self._slow_potential + self._input)
        self._fast_potential_previous = self._fast_potential
        self._slow_potential = self._next_slow_potential(self._fast_potential, self._slow_potential)

    # this is kinda made up need to look at paper
    def _update_input(self, step):
        i = self._fake_input(step)
        if i > 0:
            self._input = i
        else:
            self._input = self._input * (1 - self._input_decay)**self._step_size + i
    
    def step(self, step, unused_environment):
        self._update_voltage()
        self._update_input(step)
            
    def outputs(self):
        return {"potential": self._fast_potential, "input synapse": self._input}


def default_model():
    alpha = 1
    mu = 0.001
    sigma = 0
    sigma_next = 0
    input_decay = 0.001
    # it might make sense to drive a cell instead of a synapse
    def fake_input_spirit(step):
        if step % 10000 == 0 and step > 9999:
            return 1
        return 0
    return SpiritModel(input_decay, alpha, mu, sigma, sigma_next, fake_input_spirit)
