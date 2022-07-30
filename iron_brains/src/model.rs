pub mod cell_membrane;
use cell_membrane::CellType;
use cell_membrane::CellMembrane;
use cell_membrane::CellMembraneParameters;

pub mod synapse;
use synapse::Synapse;
use synapse::SynapseParameters;
use synapse::LayerSynapseParameters;

use pyo3::prelude::*;

#[pyclass]
pub struct Model {
    cell_membranes: std::vec::Vec<CellMembrane>,
    synapses: std::vec::Vec<Synapse>,
    cell_membrane_parameters: CellMembraneParameters,
    synapse_parameters: SynapseParameters,
    positive_synapse_indexes: std::vec::Vec<usize>,
}


impl Model {

    // all kinds of naming issues with file
    pub fn new(size: usize,
	       cell_membrane_parameters: CellMembraneParameters,
	       synapse_parameters: SynapseParameters) -> Self {
	let model = Self {
	    // size really uneeded here need it more for sysnapes
	    cell_membranes : std::vec::Vec::with_capacity(size),
	    synapses: std::vec::Vec::new(),
	    cell_membrane_parameters,
	    synapse_parameters,
	    positive_synapse_indexes: std::vec::Vec::new(),
	};
	model
    }

    pub fn add_cell(&mut self, cell_type: CellType) -> usize{
	let cell_membrane = CellMembrane::new(cell_type,
					      self.cell_membrane_parameters.starting_membrane_voltage,
					      self.cell_membrane_parameters.starting_input_current,
					      self.cell_membrane_parameters.starting_calcium);
	self.cell_membranes.push(cell_membrane);
	let index: usize = self.cell_membranes.len()  - 1;
	index
    }

    // obviously could be way faster than going over every synapse
    pub fn apply_fire(&mut self, index: usize){
	let cell = &self.cell_membranes[index];
	let output_indexes: &std::vec::Vec<usize> = &cell.output_synapse_indexes;
	let cell_type: CellType = cell.cell_type;

	let mut post_cell_indexes: std::vec::Vec<usize> = std::vec::Vec::new();
	let mut synapse_indexes: std::vec::Vec<usize> = std::vec::Vec::new();
	for synapse_index in output_indexes.iter() {
	    let synapse = &mut self.synapses[*synapse_index];
	    post_cell_indexes.push(synapse.post_cell_index);
	    synapse_indexes.push(*synapse_index)
	}

	
	for n in 0..post_cell_indexes.len() {
	    let synapse_index = synapse_indexes[n];
	    let post_cell_index = post_cell_indexes[n];
	    let synapse = &mut self.synapses[synapse_index];
	    let post_cell = &mut self.cell_membranes[post_cell_index];
	    synapse.pre_fire(cell_type, post_cell,
			     &self.synapse_parameters);
	}
	
	for synapse_index in self.cell_membranes[index].input_synapse_indexes.iter() {
	    let synapse = &mut self.synapses[*synapse_index];
	    let pre_cell = &self.cell_membranes[synapse.pre_cell_index];
	    synapse.post_fire(pre_cell,
			      &self.synapse_parameters);
	}
    }

    pub fn voltage(&self, index: usize) -> f64 {
	let cell_membrane : &CellMembrane = &self.cell_membranes[index];
	cell_membrane.voltage()
    }

    // could be made faster by creating the vector duing updates.
    // we chould do this in python too.
    pub fn fired_indexes(&self) -> std::vec::Vec<usize> {
	let mut indexes: std::vec::Vec<usize> =  std::vec::Vec::new();
	for (index, cell_membrane,) in self.cell_membranes.iter().enumerate() {
	    if cell_membrane.fired() {
		indexes.push(index);
	    };
	};
	return indexes;
    }

    pub fn receive_input(&mut self, index: usize, strength: f64) {
	self.cell_membranes[index].receive_input(strength);
    }

    pub fn update_cells(&mut self) {
	for cell_membrane in self.cell_membranes.iter_mut() {
	    cell_membrane.update(&self.cell_membrane_parameters);
	};
    }

    ////////////////

    pub fn add_synapse(&mut self,
		       layer_parameters : LayerSynapseParameters,
		       strength: f64, inhibitory_strength: f64,
		       pre_cell_index: usize, post_cell_index: usize,) -> usize {
	let synapse: Synapse = Synapse::new(layer_parameters,
					    strength, inhibitory_strength,
					    self.synapse_parameters.starting_s_tag,
					    pre_cell_index, post_cell_index);

	self.synapses.push(synapse);
	let index: usize = self.synapses.len()  - 1;
	self.cell_membranes[pre_cell_index].output_synapse_indexes.push(index);
	self.cell_membranes[post_cell_index].input_synapse_indexes.push(index);
    	if inhibitory_strength == 0.0 {
	    self.positive_synapse_indexes.push(index);
	}
	index
    }

    pub fn clear_positive_s_tags(&mut self) {
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[*index];
	    synapse.s_tag = 0.0
	}
    }


    // would be much faster with per cell indexes
    pub fn positive_normalize(&mut self, cell_index: usize, target: f64) -> f64 {
	let total = self.cell_positive_input_strength(cell_index);
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
	    if synapse.post_cell_index == cell_index {
		let keep_part = synapse.strength * keep_factor;
		let change_part = synapse.strength * change_factor;
		synapse.strength =  keep_part +  change_part;
		synapse.cap(&self.synapse_parameters);
		new_total += synapse.strength;
	    }
	}
	return new_total;
    }

    pub fn cell_positive_input_strength(&self, cell_index: usize) -> f64 {
	let mut total: f64 = 0.0;
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &Synapse = &self.synapses[*index];
	    if synapse.post_cell_index == cell_index {
		total += synapse.strength
	    };
	};
	return total;
    }

    pub fn strength(&self, index: usize,) -> f64 {
	self.synapses[index].strength
    }
    
    pub fn inhibitory_strength(&self, index: usize,) -> f64 {
	self.synapses[index].inhibitory_strength
    }

    pub fn update_strength(&mut self, index: usize, strength: f64) {
	self.synapses[index].strength = strength;
    }
    pub fn update_inhibitory_strength(&mut self, index: usize, inhibitory_strength: f64) {
	self.synapses[index].inhibitory_strength = inhibitory_strength;
    }

    pub fn update_synapses(&mut self, dopamine: f64) {
	for index in self.positive_synapse_indexes.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[*index];
	    synapse.update(&self.synapse_parameters, dopamine);
	};
    }

    pub fn cap(&mut self, index: usize) {
	self.synapses[index].cap(&self.synapse_parameters);
    }
}
