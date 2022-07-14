pub mod cell_membrane;
use cell_membrane::CellMembrane;
use cell_membrane::CellMembraneParameters;

pub mod synapse;
use synapse::Synapse;
use synapse::SynapseParameters;

use pyo3::prelude::*;
#[pyclass]
pub struct Model {
    cell_membranes: std::vec::Vec<CellMembrane>,
    cell_membrane_parameters: CellMembraneParameters,
    synapses: std::vec::Vec<Synapse>,
    positive_synapse_indexes: std::vec::Vec<usize>,
    synapse_parameters: SynapseParameters,
}

impl Model {

    // all kinds of naming issues with file
    pub fn new(size: usize) -> Self {
	let mut model = Self {
	    cell_membranes : std::vec::Vec::with_capacity(size),
	    cell_membrane_parameters: CellMembraneParameters::new(),
	    synapses: std::vec::Vec::new(),
	    positive_synapse_indexes: std::vec::Vec::new(),
	    synapse_parameters: SynapseParameters::new(),
	};
	for index in 0..size {
            model.cell_membranes.push(CellMembrane::new(index));   
	};
	model
    }

    pub fn voltage(&self, index: u32) -> f64 {
	let cell_membrane : &CellMembrane = &self.cell_membranes[index as usize];
	cell_membrane.voltage()
    }

    pub fn fired(&self, index: u32) -> bool {
	self.cell_membranes[index as usize].fired()
    }

    // could be made faster by creating the vector duing updates.
    // we chould do this in python too.
    pub fn fired_indexes(&self) -> std::vec::Vec<usize> {
	let mut indexes: std::vec::Vec<usize> =  std::vec::Vec::new();
	for cell_membrane in self.cell_membranes.iter() {
	    if cell_membrane.fired() {
		indexes.push(cell_membrane.index);
	    };
	};
	return indexes;
    }

    pub fn calcium(&self, index: u32) -> f64 {
	self.cell_membranes[index as usize].calcium()
    }

    pub fn receive_input(&mut self, index: u32, strength: f64) {
	self.cell_membranes[index as usize].receive_input(strength);
    }

    pub fn update_cells(&mut self) {
	for cell_membrane in self.cell_membranes.iter_mut() {
	    cell_membrane.update(&self.cell_membrane_parameters);
	};
    }

    ////////////////

    pub fn add_synapse(&mut self, unsupervised_stdp: bool,
		       strength: f64, inhibitory_strength: f64, cell_index: i64) -> i64{
	let synapse: Synapse = Synapse::new(unsupervised_stdp,
					    strength, inhibitory_strength, cell_index);

	self.synapses.push(synapse);
	let index: usize = self.synapses.len()  - 1;
    	if inhibitory_strength == 0.0 {
	    self.positive_synapse_indexes.push(index);
	}
	index as i64
    }

    pub fn clear_positive_s_tags(&mut self) {
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[*index];
	    synapse.s_tag = 0.0
	}
    }


    // would be much faster with per cell indexes
    pub fn positive_normalize(&mut self, cell_index: i64, target: f64) -> f64 {
	let total = self.cell_positive_strength(cell_index);
	let scale: f64 = if total > 0.0 {
	    target / total
	} else {
	    1.0
	};

	// if this is always going to be 1 we could simplify this
	let input_balance_scalar: f64 = 1.0; 
	let change_factor: f64 = scale * input_balance_scalar;
        let keep_factor: f64 = 1.0 - input_balance_scalar;
	let mut new_total: f64 = 0.0;
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[*index];
	    if synapse.cell_index() == cell_index {
		let keep_part = synapse.strength() * keep_factor;
		let change_part = synapse.strength() * change_factor;
		synapse.strength =  keep_part +  change_part;
		synapse.cap(&self.synapse_parameters);
		new_total += synapse.strength();
	    }
	}
	return new_total;
    }

    pub fn cell_positive_strength(&self, cell_index: i64) -> f64 {
	let mut total: f64 = 0.0;
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &Synapse = &self.synapses[*index];
	    if synapse.cell_index() == cell_index {
		total += synapse.strength()
	    };
	};
	return total;
    }

    pub fn s_tag(&self, index: u32,) -> f64 {
	self.synapses[index as usize].s_tag()
    }
    
    pub fn strength(&self, index: u32,) -> f64 {
	self.synapses[index as usize].strength()
    }
    
    pub fn inhibitory_strength(&self, index: u32,) -> f64 {
	self.synapses[index as usize].inhibitory_strength()
    }

    pub fn update_s_tag(&mut self, index: u32, s_tag: f64) {
	self.synapses[index as usize].update_s_tag(s_tag);
    }
    pub fn update_strength(&mut self, index: u32, strength: f64) {
	self.synapses[index as usize].update_strength(strength);
    }
    pub fn update_inhibitory_strength(&mut self, index: u32, inhibitory_strength: f64) {
	self.synapses[index as usize].update_inhibitory_strength(inhibitory_strength);
    }

    pub fn update_synapses(&mut self, dopamine: f64) {
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[*index];
	    synapse.update(&self.synapse_parameters, dopamine);
	};
    }

    pub fn cap(&mut self, index: u32) {
	self.synapses[index as usize].cap(&self.synapse_parameters);
    }

}
