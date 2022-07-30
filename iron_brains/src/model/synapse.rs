use crate::model::CellMembrane;
use crate::model::CellType;

use pyo3::prelude::*;

#[derive(Copy, Clone, PartialEq)] 
#[pyclass]
pub struct SynapseParameters {
    stdp_scalar: f64,
    max_strength: f64,
    min_strength: f64,
    pub starting_s_tag: f64,
    noise_factor: f64,
}

#[pymethods]
impl SynapseParameters {
    #[new]
    pub fn new(stdp_scalar: f64,
	       max_strength: f64, min_strength: f64,
	       starting_s_tag: f64, noise_factor: f64) -> Self {
	Self {
	    stdp_scalar,
	    max_strength,
	    min_strength,
	    starting_s_tag,
	    noise_factor,
	}
    }
}

// for now a copy is held by each cell
#[derive(Copy, Clone, PartialEq)] 
#[pyclass]
pub struct LayerSynapseParameters {
    unsupervised_stdp: bool,
    reward_scalar: f64,
    s_tag_decay_rate: f64,
}

#[pymethods]
impl LayerSynapseParameters {
    #[new]
    pub fn new(unsupervised_stdp: bool,
	       reward_scalar: f64,
	       s_tag_decay_rate: f64,
	       ) -> Self {
	Self {
	    unsupervised_stdp,
	    reward_scalar,
	    s_tag_decay_rate,
	}
    }
}

pub struct Synapse {
    layer_parameters : LayerSynapseParameters,
    pub strength: f64,
    pub inhibitory_strength: f64,
    pub s_tag: f64,
    pub pre_cell_index: usize,
    pub post_cell_index: usize,
}

impl Synapse {
    pub fn new(layer_parameters : LayerSynapseParameters,
	       strength: f64, inhibitory_strength: f64,
	       s_tag: f64,
	       pre_cell_index: usize,
	       post_cell_index: usize) -> Self {
	Self {
	    layer_parameters,
	    strength,
	    inhibitory_strength,
	    s_tag,
	    pre_cell_index,
	    post_cell_index,
	}
    }

    pub fn update(&mut self, synapse_parameters: &SynapseParameters, dopamine: f64) {
	if self.s_tag != 0.0 {
	    self.s_tag = self.s_tag * (1.0 - self.layer_parameters.s_tag_decay_rate);
            if self.layer_parameters.unsupervised_stdp {
		self.strength += self.s_tag * self.layer_parameters.reward_scalar * 0.1;
            } else {
		self.strength += self.s_tag * dopamine * self.layer_parameters.reward_scalar;
	    };
            self.cap(synapse_parameters);
	};
    }

    pub fn pre_fire(&mut self, pre_cell_type: CellType, post_cell: &mut CellMembrane,
		    synapse_parameters: &SynapseParameters) {
	if pre_cell_type == CellType::INHIBIT {
            post_cell.receive_input(self.inhibitory_strength * -1.0);
	}
	if pre_cell_type == CellType::EXCITE {
	    self.s_tag -= synapse_parameters.stdp_scalar * post_cell.calcium();

            if synapse_parameters.noise_factor > 0.0 {
		let random: f64 = (rand::random::<f64>() * 2.0) - 1.0;
                let noise = synapse_parameters.noise_factor * random * self.strength;
                post_cell.receive_input(self.strength + noise);
            } else {
                post_cell.receive_input(self.strength);
	    }
	}
    }

    pub fn post_fire(&mut self, pre_cell: &CellMembrane, synapse_parameters: &SynapseParameters) {
	if pre_cell.cell_type == CellType::INHIBIT{
            return;
	}

        self.s_tag += synapse_parameters.stdp_scalar * pre_cell.calcium();

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