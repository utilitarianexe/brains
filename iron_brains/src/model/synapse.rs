pub struct SynapseParameters {
    reward_scalar: f64,
    s_tag_decay_rate: f64,
    max_strength: f64,
    min_strength: f64,
}

impl SynapseParameters {
    pub fn default_synapse_parameters() -> SynapseParameters {
	SynapseParameters {
	    reward_scalar: 0.1,
	    s_tag_decay_rate: 0.002,
	    max_strength: 0.4,
	    min_strength: 0.0,
	}
    }

}

pub struct Synapse {
    unsupervised_stdp: bool,
    pub strength: f64,
    inhibitory_strength: f64,
    s_tag: f64,
    cell_index: i64
}

impl Synapse {

    pub fn default_synapse(unsupervised_stdp: bool,
			   strength: f64, inhibitory_strength: f64, cell_index: i64) -> Synapse {
	Synapse {
	    unsupervised_stdp,
	    strength,
	    inhibitory_strength,
	    s_tag: 0.0,
	    cell_index,
	}
    }

    pub fn cell_index(&self) -> i64 {
	self.cell_index
    }

    pub fn s_tag(&self) -> f64 {
	self.s_tag
    }
    
    pub fn strength(&self) -> f64 {
	self.strength
    }
    
    pub fn inhibitory_strength(&self) -> f64 {
	self.inhibitory_strength
    }

    pub fn update_s_tag(&mut self, s_tag: f64) {
	self.s_tag = s_tag;
    }
    pub fn update_strength(&mut self, strength: f64) {
	self.strength = strength;
    }
    pub fn update_inhibitory_strength(&mut self, inhibitory_strength: f64) {
	self.inhibitory_strength = inhibitory_strength;
    }

    pub fn update(&mut self, synapse_parameters: &SynapseParameters, dopamine: f64) {
	if self.s_tag != 0.0 {
	    self.s_tag = self.s_tag * (1.0 - synapse_parameters.s_tag_decay_rate);
            if self.unsupervised_stdp {
		self.strength += self.s_tag * synapse_parameters.reward_scalar;
            } else {
		self.strength += self.s_tag * dopamine * synapse_parameters.reward_scalar;
	    };
            self.cap(synapse_parameters);
	};
    }

    pub fn cap(&mut self, synapse_parameters: &SynapseParameters) {
	// could use matches here
        if self.strength >= synapse_parameters.max_strength {
            self.strength = synapse_parameters.max_strength;
	};
        
        if self.strength < synapse_parameters.min_strength {
            self.strength = synapse_parameters.min_strength;
	};

        if self.inhibitory_strength >= synapse_parameters.max_strength {
            self.inhibitory_strength = synapse_parameters.max_strength;
	};
            
        if self.inhibitory_strength < synapse_parameters.min_strength {
            self.inhibitory_strength = synapse_parameters.min_strength;
	};
    }
}
