pub mod cell_membrane;
use cell_membrane::CellType;
use cell_membrane::CellMembrane;
use cell_membrane::CellMembraneParameters;

pub mod synapse;
use synapse::Synapse;
use synapse::SynapseParameters;
use synapse::LayerSynapseParameters;

pub mod network;
use network::Network;

use pyo3::prelude::*;

#[pyclass]
pub struct Model {
    cell_membranes: std::vec::Vec<CellMembrane>,
    synapses: std::vec::Vec<Synapse>,
    cell_membrane_parameters: CellMembraneParameters,
    synapse_parameters: SynapseParameters,
    network: Network,
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
	    network: Network::new(size),
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
	for connection in self.network.outgoing_connections(index) {
	    let synapse = &mut self.synapses[connection.synapse_index];
	    let post_cell = &mut self.cell_membranes[connection.post_cell_index];
	    let strength = synapse.pre_fire(post_cell.calcium(), &self.synapse_parameters);
	    post_cell.receive_input(strength);
	}
	
	for connection in self.network.incoming_connections(index) {
	    let synapse = &mut self.synapses[connection.synapse_index];
	    let pre_cell = &self.cell_membranes[connection.pre_cell_index];
	    synapse.post_fire(pre_cell.calcium(),
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
					    self.cell_membranes[pre_cell_index].cell_type);
	let positive: bool = synapse.pre_cell_type == CellType::EXCITE;
	self.synapses.push(synapse);
	self.network.connect(pre_cell_index, post_cell_index, self.synapses.len() - 1, positive);
	let index: usize = self.synapses.len()  - 1;
	index
    }

    pub fn clear_positive_s_tags(&mut self) {
	for connection in self.network.positive_connections.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[connection.synapse_index];
	    synapse.s_tag = 0.0
	}
    }


    // would be much faster with positive only synapse indexes
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
	for connection in self.network.incoming_connections(cell_index) {
	    let synapse: &mut Synapse = &mut self.synapses[connection.synapse_index];
	    if synapse.pre_cell_type == CellType::EXCITE {
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
	for connection in self.network.incoming_connections(cell_index) {
	    let synapse: &Synapse = &self.synapses[connection.synapse_index];
	    total += synapse.strength
	}
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
	for connection in self.network.positive_connections.iter() {
	    let synapse: &mut Synapse = &mut self.synapses[connection.synapse_index];
	    synapse.update(&self.synapse_parameters, dopamine);
	};
    }

    pub fn cap(&mut self, index: usize) {
	self.synapses[index].cap(&self.synapse_parameters);
    }
}
