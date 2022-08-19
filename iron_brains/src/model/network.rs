use std::vec::Vec;


#[derive(Copy, Clone, PartialEq)] 
pub struct Connection {
    pub pre_cell_index: usize,
    pub post_cell_index: usize,
    pub synapse_index: usize,
}

pub struct Network {
    connections: Vec<Connection>,
    // I really hate that I can't use references in these but would require lifetimes.
    // Which then make this incompatible with pyo3
    outgoing_connections_by_index: Vec<Vec<Connection>>,
    incoming_connections_by_index: Vec<Vec<Connection>>,
}


impl Network {
    pub fn new(size: usize) -> Self {
	let mut network = Self {
	    connections: Vec::new(),
	    outgoing_connections_by_index: Vec::with_capacity(size),
	    incoming_connections_by_index: Vec::with_capacity(size)
	};
	for _i in 0..size {
	    network.outgoing_connections_by_index.push(Vec::new());
	    network.incoming_connections_by_index.push(Vec::new());
	}
	return network;
    }

    pub fn connect(&mut self, pre_cell_index: usize, post_cell_index: usize, synapse_index: usize) {
	let connection = Connection {
	    pre_cell_index: pre_cell_index,
	    post_cell_index: post_cell_index,
	    synapse_index: synapse_index,
	};
	self.connections.push(connection);
	self.outgoing_connections_by_index[pre_cell_index].push(connection);
	self.incoming_connections_by_index[post_cell_index].push(connection);
    }

    pub fn outgoing_connections(&self, cell_index: usize) -> &Vec<Connection> {
	&self.outgoing_connections_by_index[cell_index]
    }

    pub fn incoming_connections(&self, cell_index: usize) -> &Vec<Connection> {
	&self.incoming_connections_by_index[cell_index]
    }

}
